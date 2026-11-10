"""Session-local adapter for the Step 5 chat loop; no shared agent changes."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any
from uuid import uuid4

import requests

from chat import now_iso, run_model_tool_loop, safe_slug, trim_history, write_transcript
from providers import make_provider
from providers.base import ModelResponse
from tools import TOOL_FUNCTIONS, to_openai_tools
from tools.send.tool import send_telegram
from ui_data import VersionSnapshot, resolve_snapshot

ROOT = Path(__file__).resolve().parent


def credential_values() -> set[str]:
    return {value for name, value in os.environ.items()
            if any(part in name.upper() for part in ("KEY", "TOKEN", "SECRET")) and len(value) >= 6}


def public_data(value: Any, *, secrets: set[str] | None = None) -> Any:
    """Keep configured credentials out of UI output and exported transcripts."""
    payload = json.dumps(value, ensure_ascii=False, default=str)
    for secret in sorted(credential_values() | (secrets or set()), key=len, reverse=True):
        payload = payload.replace(json.dumps(secret, ensure_ascii=False)[1:-1], "[REDACTED]")
    # Also sanitize Telegram tokens in copied errors, even after key rotation.
    payload = re.sub(r"\b\d{6,}:[A-Za-z0-9_-]{20,}\b", "[REDACTED]", payload)
    return json.loads(payload)


def provider_problem(name: str, *, probe_ollama: bool = False) -> str | None:
    key_names = {"gemini": "GEMINI_API_KEY", "openrouter": "OPENROUTER_API_KEY",
                 "openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY"}
    if name in key_names:
        key = os.getenv(key_names[name], "").strip()
        if not key or key in {"...", "your_api_key", "your-key-here"}:
            return f"Chưa cấu hình {key_names[name]} trong .env trên máy chạy demo."
    elif name == "ollama" and probe_ollama:
        base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1").rstrip("/")
        try:
            response = requests.get(base + "/models", timeout=3)
            response.raise_for_status()
            if not isinstance(response.json().get("data"), list):
                return "Endpoint Ollama chưa trả danh sách model hợp lệ. Kiểm tra OLLAMA_BASE_URL."
        except requests.RequestException:
            return "Không kết nối được Ollama. Khởi động Ollama (ollama serve) và kiểm tra OLLAMA_BASE_URL trên máy chạy demo."
        except (ValueError, AttributeError):
            return "Endpoint Ollama trả dữ liệu không hợp lệ. Kiểm tra OLLAMA_BASE_URL."
    return None


def friendly_error(error: str, provider_name: str = "") -> str:
    if "429" in error or "RESOURCE_EXHAUSTED" in error:
        return "Dịch vụ AI đã chạm hạn mức. Chờ hạn mức làm mới hoặc chọn provider/model còn quota."
    if "503" in error or "UNAVAILABLE" in error:
        return "Dịch vụ AI đang quá tải. Hãy thử lại sau hoặc chọn model khác."
    if "10013" in error:
        return "Tiến trình demo đang bị chặn kết nối mạng. Khởi động Streamlit với quyền truy cập Internet."
    if provider_name == "ollama" and any(word in error.lower() for word in ("connect", "refused", "10061")):
        return "Không kết nối được Ollama. Hãy chạy Ollama trên máy chủ demo và thử lại."
    if provider_name == "ollama" and ("404" in error or "not found" in error.lower()):
        return "Ollama chưa có model đã chọn. Tải model bằng ollama pull <tên-model>."
    if "401" in error or "API_KEY_INVALID" in error or "403" in error:
        return "Dịch vụ từ chối xác thực. Kiểm tra API key và quyền sử dụng model trên máy chạy demo."
    if "Chưa cấu hình" in error or "Ollama" in error:
        return error
    return "Yêu cầu chưa hoàn thành. Mở chi tiết để xem lỗi của provider hoặc tool."


class SendPreviewProvider:
    """Pause a model-requested send before the shared loop can execute it."""

    def __init__(self, provider: Any) -> None:
        self.provider = provider
        self.pending: dict[str, Any] | None = None
        self.error: str | None = None
        self.actual_models: list[str] = []

    def complete(self, *args: Any, **kwargs: Any) -> ModelResponse:
        try:
            response = self.provider.complete(*args, **kwargs)
        except Exception as exc:
            # End the loop with an explicit UI error so completed tool rounds
            # remain in the transcript when a later model request fails.
            self.error = public_data(f"{type(exc).__name__}: {exc}")
            return ModelResponse(text="Dịch vụ AI chưa xử lý được yêu cầu. Bạn có thể thử lại sau.")
        raw = response.raw
        actual_model = next((raw.get(key) if isinstance(raw, dict) else getattr(raw, key, None)
                             for key in ("model", "model_version")
                             if (raw.get(key) if isinstance(raw, dict) else getattr(raw, key, None))), None)
        if isinstance(actual_model, str) and actual_model not in self.actual_models:
            self.actual_models.append(actual_model)
        sends = [call for call in response.tool_calls if TOOL_FUNCTIONS.get(call.name) is send_telegram]
        if sends:
            # Preserve every original call: the UI gate is separate from model output.
            self.pending = {
                "tool": sends[0].name,
                "text": public_data(sends[0].args.get("text", "")),
                "requested_tool_calls": [
                    {"name": call.name, "args": call.args} for call in response.tool_calls
                ],
                "model_assistant_text": response.text,
            }
            return ModelResponse(text="Bản nháp đã sẵn sàng. Hãy xem nội dung và chọn xác nhận gửi hoặc hủy.")
        return response


class DemoSession:
    def __init__(
        self, *, provider_name: str = "gemini", model: str | None = None,
        version: str = "v0", provider: Any | None = None,
        transcripts_dir: Path | None = None,
        snapshot: VersionSnapshot | None = None,
    ) -> None:
        self.provider = provider if provider is not None else make_provider(provider_name)
        self.provider_name = provider_name
        self.check_configuration = provider is None
        self.secrets = credential_values()
        self.model = model or getattr(self.provider, "default_model", None)
        self.snapshot = snapshot or resolve_snapshot(version, ROOT)
        if self.snapshot.version != version:
            raise ValueError("Snapshot không thuộc phiên bản đã chọn.")
        self.system_prompt = self.snapshot.prompt
        self.tools = to_openai_tools(self.snapshot.declarations)
        session_id = f"{safe_slug(version)}_{safe_slug(provider_name)}_ui_{uuid4().hex}"
        self.path = (transcripts_dir or ROOT / "transcripts") / f"{session_id}.transcript.json"
        self.history: list[dict[str, str]] = []
        self.pending_send: dict[str, Any] | None = None
        self.transcript: dict[str, Any] = {
            "transcript_id": session_id,
            **self.snapshot.evidence,
            "provider": provider_name,
            "model": self.model,
            "requested_model": self.model,
            "actual_model": None,
            "interface": "streamlit",
            "ui_send_confirmation": True,
            "system_prompt": self.snapshot.prompt_source,
            "tools": self.snapshot.tools_source,
            "history_window": 5,
            "max_tool_rounds": 4,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "turns": [],
        }

    def save(self) -> None:
        self.transcript["updated_at"] = now_iso()
        write_transcript(self.path, public_data(self.transcript, secrets=self.secrets))

    def submit(self, user_text: str) -> dict[str, Any]:
        if self.pending_send is not None:
            raise ValueError("Hãy xác nhận hoặc hủy bản nháp trước khi gửi câu hỏi mới.")
        user_text = user_text.strip()
        if not user_text:
            raise ValueError("Vui lòng nhập câu hỏi.")
        record: dict[str, Any] = {
            "turn_index": len(self.transcript["turns"]) + 1,
            "started_at": now_iso(), "user": user_text,
            "rounds": [], "tool_events": [],
        }
        gate = SendPreviewProvider(self.provider)
        try:
            problem = provider_problem(self.provider_name, probe_ollama=True) if self.check_configuration else None
            if problem:
                raise ValueError(problem)
            result = run_model_tool_loop(
                provider=gate,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    *trim_history(self.history, 5),
                    {"role": "user", "content": user_text},
                ],
                tools=self.tools, model=self.model, max_tool_rounds=4,
                log_tool_calls=False,
            )
            record.update(result)
            record["actual_models"] = gate.actual_models
            if gate.actual_models:
                self.transcript["actual_model"] = public_data(gate.actual_models[-1], secrets=self.secrets)
            if gate.error is not None:
                record.update({"status": "provider_error", "error": gate.error,
                               "ui_provider_error": True})
            if gate.pending is not None:
                record["status"] = "waiting_for_confirmation"
                record["ui_action_gate"] = public_data(gate.pending)
                record["ui_action_gate"]["decision"] = "pending"
                self.pending_send = {**gate.pending, "turn_index": record["turn_index"]}
        except Exception as exc:
            record.update({
                "status": "provider_error", "assistant_text": "Không thể hoàn thành yêu cầu lúc này.",
                "error": public_data(f"{type(exc).__name__}: {exc}"),
            })
        record["ended_at"] = now_iso()
        record = public_data(record, secrets=self.secrets)
        self.transcript["turns"].append(record)
        self.history.extend([
            {"role": "user", "content": record["user"]},
            {"role": "assistant", "content": record["assistant_text"]},
        ])
        self.save()
        return record

    def resolve_send(self, *, confirmed: bool, reason: str = "user") -> None:
        if self.pending_send is None:
            raise ValueError("Không có bản nháp đang chờ xác nhận.")
        pending = self.pending_send
        if confirmed:
            if not isinstance(pending["text"], str) or not pending["text"].strip():
                raise ValueError("Bản nháp không có nội dung hợp lệ.")
            if not all(os.getenv(name) for name in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")):
                raise ValueError("Chưa cấu hình Telegram trên máy chủ demo.")
            try:
                result = send_telegram(text=pending["text"], confirmed=True)
            except Exception as exc:
                result = {"error": type(exc).__name__, "message": str(exc)}
            status = "sent" if result.get("status") == "sent" else "send_error"
            answer = "Đã gửi bản tin lên Telegram." if status == "sent" else "Gửi Telegram chưa thành công. Xem chi tiết lỗi bên dưới."
        else:
            result = {"status": "cancelled"}
            status, answer = "cancelled", "Đã hủy gửi bản tin."
        record = self.transcript["turns"][pending["turn_index"] - 1]
        record["status"] = status
        record["assistant_text"] += "\n\n" + answer
        record["ui_action_gate"].update({
            "decision": "confirmed" if confirmed else "cancelled",
            "decision_reason": reason,
            "decided_at": now_iso(), "result": public_data(result),
        })
        if confirmed:
            record["tool_events"].append(public_data({
                "tool": pending["tool"], "args": {"text": pending["text"], "confirmed": True},
                "result": result, "origin": "ui_confirmation",
            }))
        record["ended_at"] = now_iso()
        self.history[-1]["content"] = record["assistant_text"]
        self.pending_send = None
        self.save()

    def export_json(self) -> str:
        return json.dumps(public_data(self.transcript, secrets=self.secrets), ensure_ascii=False, indent=2, default=str)


class VersionSessions:
    """One current conversation and remembered settings per version, per browser."""

    def __init__(self) -> None:
        self.sessions: dict[str, DemoSession] = {}
        self.preferences: dict[str, dict[str, str]] = {}

    def select(self, version: str, provider: str, model: str,
               snapshot: VersionSnapshot | None) -> DemoSession | None:
        session = self.sessions.get(version)
        if session and (session.provider_name != provider or session.model != model
                        or (snapshot and session.snapshot.hashes != snapshot.hashes)):
            self.reset(version, reason="configuration_changed")
            return None
        return session

    def reset(self, version: str, *, reason: str = "new_conversation") -> None:
        session = self.sessions.get(version)
        if session and session.pending_send is not None:
            session.resolve_send(confirmed=False, reason=reason)
        self.sessions.pop(version, None)
