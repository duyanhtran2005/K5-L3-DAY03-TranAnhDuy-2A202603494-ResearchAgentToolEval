"""Session-local adapter for the Step 5 chat loop; no shared agent changes."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from chat import now_iso, run_model_tool_loop, safe_slug, trim_history, write_transcript
from providers import make_provider
from providers.base import ModelResponse
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
from tools.send.tool import send_telegram
from versioning import artifact_version_dict, build_artifact_version

ROOT = Path(__file__).resolve().parent


def public_data(value: Any) -> Any:
    """Keep configured credentials out of UI output and exported transcripts."""
    payload = json.dumps(value, ensure_ascii=False, default=str)
    secrets = {
        value for name, value in os.environ.items()
        if any(part in name.upper() for part in ("KEY", "TOKEN", "SECRET"))
        and len(value) >= 8
    }
    for secret in sorted(secrets, key=len, reverse=True):
        payload = payload.replace(json.dumps(secret, ensure_ascii=False)[1:-1], "[REDACTED]")
    return json.loads(payload)


class SendPreviewProvider:
    """Pause a model-requested send before the shared loop can execute it."""

    def __init__(self, provider: Any) -> None:
        self.provider = provider
        self.pending: dict[str, Any] | None = None
        self.error: str | None = None

    def complete(self, *args: Any, **kwargs: Any) -> ModelResponse:
        try:
            response = self.provider.complete(*args, **kwargs)
        except Exception as exc:
            # End the loop with an explicit UI error so completed tool rounds
            # remain in the transcript when a later model request fails.
            self.error = public_data(f"{type(exc).__name__}: {exc}")
            return ModelResponse(text="Dịch vụ AI chưa xử lý được yêu cầu. Bạn có thể thử lại sau.")
        sends = [call for call in response.tool_calls if TOOL_FUNCTIONS.get(call.name) is send_telegram]
        if sends:
            # Preserve every original call: the UI gate is separate from model output.
            self.pending = {
                "tool": sends[0].name,
                "text": sends[0].args.get("text", ""),
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
    ) -> None:
        self.provider = provider if provider is not None else make_provider(provider_name)
        self.model = model or getattr(self.provider, "default_model", None)
        self.system_prompt = (ROOT / "artifacts/system_prompt.md").read_text(encoding="utf-8")
        tools_path = ROOT / "artifacts/tools.yaml"
        self.tools = to_openai_tools(load_tool_declarations(tools_path))
        version_info = build_artifact_version(version, ROOT / "artifacts/system_prompt.md", tools_path)
        session_id = f"{safe_slug(version)}_{safe_slug(provider_name)}_ui_{uuid4().hex}"
        self.path = (transcripts_dir or ROOT / "transcripts") / f"{session_id}.transcript.json"
        self.history: list[dict[str, str]] = []
        self.pending_send: dict[str, Any] | None = None
        self.transcript: dict[str, Any] = {
            "transcript_id": session_id,
            **artifact_version_dict(version_info),
            "provider": provider_name,
            "model": self.model,
            "interface": "streamlit",
            "ui_send_confirmation": True,
            "system_prompt": str(ROOT / "artifacts/system_prompt.md"),
            "tools": str(tools_path),
            "history_window": 5,
            "max_tool_rounds": 4,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "turns": [],
        }

    def save(self) -> None:
        self.transcript["updated_at"] = now_iso()
        write_transcript(self.path, public_data(self.transcript))

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
            result = run_model_tool_loop(
                provider=gate,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    *trim_history(self.history, 5),
                    {"role": "user", "content": user_text},
                ],
                tools=self.tools, model=self.model, max_tool_rounds=4,
            )
            record.update(result)
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
        record = public_data(record)
        self.transcript["turns"].append(record)
        self.history.extend([
            {"role": "user", "content": record["user"]},
            {"role": "assistant", "content": record["assistant_text"]},
        ])
        self.save()
        return record

    def resolve_send(self, *, confirmed: bool) -> None:
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
        return json.dumps(public_data(self.transcript), ensure_ascii=False, indent=2, default=str)
