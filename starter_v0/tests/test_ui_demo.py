"""Behavior checks for multi-turn UI sessions; no model or network calls."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import ui_session
from providers.base import ModelResponse, ToolCall
from ui_session import DemoSession


class ScriptedProvider:
    default_model = "fake-model"

    def __init__(self, *responses):
        self.responses = iter(responses)
        self.requests = []

    def complete(self, messages, tools=None, **kwargs):
        self.requests.append(list(messages))
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return response


def test_clarification_followup_uses_history_and_saves_full_transcript(tmp_path):
    provider = ScriptedProvider(
        ModelResponse(tool_calls=[ToolCall("clarify", {"question": "URL nào?"})]),
        ModelResponse(text="Đã nhận URL bạn bổ sung."),
    )
    session = DemoSession(provider=provider, transcripts_dir=tmp_path)
    first = session.submit("Tóm tắt bài viết này")
    assert first["status"] == "waiting_for_user"
    assert first["tool_events"][0]["tool"] == "clarify"
    session.submit("https://example.com/article")
    assert provider.requests[1][1:3] == [
        {"role": "user", "content": "Tóm tắt bài viết này"},
        {"role": "assistant", "content": "URL nào?"},
    ]
    saved = json.loads(session.path.read_text(encoding="utf-8"))
    assert len(saved["turns"]) == 2
    assert saved["prompt_hash"] and saved["tools_hash"]
    assert saved["interface"] == "streamlit"


def test_sessions_have_independent_history_and_files(tmp_path):
    one = DemoSession(provider=ScriptedProvider(ModelResponse(text="Một")), transcripts_dir=tmp_path)
    two = DemoSession(provider=ScriptedProvider(ModelResponse(text="Hai")), transcripts_dir=tmp_path)
    one.submit("Phiên một")
    assert one.path != two.path
    assert two.history == []
    assert two.transcript["turns"] == []
    assert not two.path.exists()


def test_error_is_saved_and_credentials_are_redacted(tmp_path, monkeypatch):
    secret = "fake-private-gemini-key-123456"
    monkeypatch.setenv("GEMINI_API_KEY", secret)
    provider = ScriptedProvider(RuntimeError(f"Invalid credential {secret}"), ModelResponse(text="Đã thử lại"))
    session = DemoSession(provider=provider, transcripts_dir=tmp_path)
    first = session.submit("Tìm tin")
    assert first["status"] == "provider_error"
    assert secret not in session.export_json()
    assert secret not in session.path.read_text(encoding="utf-8")
    assert "[REDACTED]" in first["error"]
    assert session.submit("Thử lại")["status"] == "answered"


def test_model_cannot_send_even_when_it_sets_confirmed_true(tmp_path, monkeypatch):
    attempts = []

    def sender(**kwargs):
        attempts.append(kwargs)
        return {"status": "sent"}

    monkeypatch.setattr(ui_session, "send_telegram", sender)
    monkeypatch.setitem(ui_session.TOOL_FUNCTIONS, "send", sender)
    provider = ScriptedProvider(ModelResponse(tool_calls=[
        ToolCall("send", {"text": "Bản nháp", "confirmed": True}),
    ]))
    session = DemoSession(provider=provider, transcripts_dir=tmp_path)
    turn = session.submit("Gửi bản tin")
    assert attempts == []
    assert turn["status"] == "waiting_for_confirmation"
    assert turn["ui_action_gate"]["requested_tool_calls"][0]["args"]["confirmed"] is True
    with pytest.raises(ValueError, match="xác nhận hoặc hủy"):
        session.submit("Câu hỏi khác")
    session.resolve_send(confirmed=False)
    assert attempts == []
    assert session.pending_send is None
    assert session.transcript["turns"][0]["status"] == "cancelled"


def test_late_provider_error_preserves_completed_tool_rounds(tmp_path):
    provider = ScriptedProvider(
        ModelResponse(tool_calls=[ToolCall("format", {
            "items": [{"title": "Tin demo", "url": "https://example.com"}], "template": "bullets",
        })]),
        RuntimeError("503 service unavailable"),
    )
    session = DemoSession(provider=provider, transcripts_dir=tmp_path)
    turn = session.submit("Tạo bản tin")
    assert turn["status"] == "provider_error"
    assert turn["tool_events"][0]["tool"] == "format"
    assert len(turn["rounds"]) == 2
    assert turn["ui_provider_error"] is True


def test_explicit_confirmation_sends_once_and_records_decision(tmp_path, monkeypatch):
    attempts = []

    def sender(**kwargs):
        attempts.append(kwargs)
        return {"status": "sent"}

    monkeypatch.setattr(ui_session, "send_telegram", sender)
    monkeypatch.setitem(ui_session.TOOL_FUNCTIONS, "send", sender)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "fake-channel")
    provider = ScriptedProvider(ModelResponse(tool_calls=[ToolCall("send", {"text": "Bản nháp"})]))
    session = DemoSession(provider=provider, transcripts_dir=tmp_path)
    session.submit("Gửi bản tin")
    session.resolve_send(confirmed=True)
    assert attempts == [{"text": "Bản nháp", "confirmed": True}]
    assert session.transcript["turns"][0]["ui_action_gate"]["decision"] == "confirmed"
    with pytest.raises(ValueError, match="Không có bản nháp"):
        session.resolve_send(confirmed=True)
    assert len(attempts) == 1


def test_missing_telegram_configuration_keeps_draft_pending(tmp_path):
    provider = ScriptedProvider(ModelResponse(tool_calls=[ToolCall("send", {"text": "Bản nháp"})]))
    session = DemoSession(provider=provider, transcripts_dir=tmp_path)
    session.submit("Gửi bản tin")
    with pytest.raises(ValueError, match="Chưa cấu hình Telegram"):
        session.resolve_send(confirmed=True)
    assert session.pending_send is not None
    assert session.transcript["turns"][0]["ui_action_gate"]["decision"] == "pending"


def test_streamlit_chat_and_new_conversation(tmp_path, monkeypatch):
    AppTest = pytest.importorskip("streamlit.testing.v1", reason="Install requirements-ui.txt for UI checks").AppTest
    real_session = DemoSession
    provider = ScriptedProvider(
        ModelResponse(tool_calls=[ToolCall("clarify", {"question": "Bạn muốn đọc URL nào?"})]),
        ModelResponse(text="Tôi đã nhận URL ở lượt tiếp theo."),
    )
    monkeypatch.setattr(ui_session, "DemoSession", lambda **kwargs: real_session(
        **kwargs, provider=provider, transcripts_dir=tmp_path,
    ))
    app = AppTest.from_file(str(Path(ui_session.ROOT) / "app.py")).run(timeout=15)
    assert not app.exception
    app.chat_input[0].set_value("Tóm tắt bài viết này").run(timeout=15)
    assert not app.exception
    assert len(app.chat_message) == 2
    app.chat_input[0].set_value("https://example.com/article").run(timeout=15)
    assert not app.exception
    assert len(app.chat_message) == 4
    transcript_path = app.session_state["demo_session"].path
    assert len(json.loads(transcript_path.read_text(encoding="utf-8"))["turns"]) == 2
    app.sidebar.button[0].click().run(timeout=15)
    assert not app.exception
    assert len(app.chat_message) == 0
    assert transcript_path.exists()
