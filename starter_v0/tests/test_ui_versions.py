"""Acceptance checks for versioned evidence, session isolation and UI actions."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import requests

import ui_data
import ui_session
from providers.base import ModelResponse, ToolCall
from tools import TOOL_FUNCTIONS
from ui_data import comparison_rows, latest_runs, read_runs, resolve_snapshot, tool_inventory
from ui_session import DemoSession, VersionSessions, provider_problem

APP_PATH = ui_session.ROOT / "app.py"


def test_group_v1_snapshot_matches_run_and_exposes_compare_sources():
    snapshot = resolve_snapshot("group-v1")
    run_path = next((ui_data.ROOT / "runs").glob("group-v1_B_group_openrouter_*.json"))
    run = json.loads(run_path.read_text(encoding="utf-8"))
    assert snapshot.hashes == (run["prompt_hash"], run["tools_hash"])
    inventory = tool_inventory(snapshot.declarations, TOOL_FUNCTIONS)
    compare = next(row for row in inventory if row["Tool"] == "compare_sources")
    assert compare["Trạng thái"] == "Sẵn sàng"


@pytest.fixture
def version_root(tmp_path):
    root = tmp_path / "lab"
    versions = {}
    tools_bytes = (ui_session.ROOT / "artifacts/tools.yaml").read_bytes()
    for version in ui_data.VERSIONS:
        folder = root / "artifacts/versions" / version
        folder.mkdir(parents=True)
        (folder / "system_prompt.md").write_text(f"Prompt riêng của {version}.", encoding="utf-8")
        (folder / "tools.yaml").write_bytes(tools_bytes)
        versions[version] = {"prompt": f"artifacts/versions/{version}/system_prompt.md",
                             "tools": f"artifacts/versions/{version}/tools.yaml"}
    (root / "ui_versions.json").write_text(json.dumps({"versions": versions}), encoding="utf-8")
    return root


def write_run(root, version="v0", suffix="a", **overrides):
    folder = root / "runs"
    folder.mkdir(exist_ok=True)
    snapshot = resolve_snapshot(version, root)
    data = {"version": version, "suite": "base", "provider": "gemini", "model": "fake-model",
            "dataset_id": "base-data", "generated_at": "2026-11-10T10:00:00",
            **snapshot.evidence,
            "summary": {"case_accuracy": .5, "tool_routing_accuracy": .75,
                        "argument_accuracy": 0, "multiturn_accuracy": None,
                        "total_cases": 4, "measured_cases": 4, "provider_error_cases": 0}, **overrides}
    path = folder / f"{version}_{suffix}.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_comparison_reads_latest_runs_without_mixing_cohorts(version_root):
    write_run(version_root)
    newer = write_run(version_root, suffix="new", generated_at="2026-11-10T11:00:00")
    write_run(version_root, suffix="other", provider="openrouter", generated_at="2026-11-10T12:00:00")
    write_run(version_root, "v2")
    (version_root / "runs/broken.json").write_text("{", encoding="utf-8")
    runs, errors = read_runs(version_root)
    assert len(runs) == 4 and len(errors) == 1
    selected = latest_runs(runs, ("base", "gemini", "fake-model", "base-data"))
    assert selected["v0"].path == newer
    rows = comparison_rows(selected)
    assert rows[0]["Pass"] == "50.00%"
    assert rows[0]["Routing"] == "75.00%"
    assert rows[0]["Arguments"] == "0.00%"
    assert rows[0]["Multi-turn"] == "—"
    assert rows[1]["Pass"] == "—" and rows[1]["Run JSON"] == "Chưa có run"
    assert [row["Version"] for row in rows] == ["v0", "v1", "v2", "v3"]


def test_run_with_no_measured_cases_is_not_presented_as_zero_accuracy(version_root):
    write_run(version_root, summary={"measured_cases": 0, "total_cases": 4,
                                    "provider_error_cases": 4, "case_accuracy": 0})
    runs, _ = read_runs(version_root)
    row = comparison_rows(latest_runs(runs, runs[0].cohort))[0]
    assert row["Pass"] == "—" and row["Lỗi provider"] == "4"


def test_snapshot_must_match_run_hash_and_missing_versions_are_blocked(version_root):
    write_run(version_root, "v2")
    runs, _ = read_runs(version_root)
    original = resolve_snapshot("v2", version_root, runs[0])
    (version_root / "artifacts/versions/v2/system_prompt.md").write_text("Changed prompt", encoding="utf-8")
    with pytest.raises(ValueError, match="không khớp prompt_hash"):
        resolve_snapshot("v2", version_root, runs[0])
    assert original.prompt == "Prompt riêng của v2."
    with pytest.raises(ValueError, match="Chưa có snapshot"):
        resolve_snapshot("v3", version_root / "empty")


def test_run_paths_are_rebased_and_validated_by_hash(version_root):
    snapshot = resolve_snapshot("v1", version_root)
    archive = version_root / "saved"
    archive.mkdir()
    (archive / "v1.md").write_bytes(snapshot.prompt_bytes)
    (archive / "v1.yaml").write_bytes(snapshot.tools_bytes)
    write_run(version_root, "v1", system_prompt="C:/teammate/starter_v0/saved/v1.md",
              tools="C:/teammate/starter_v0/saved/v1.yaml")
    # Remove mappings from the UI config, without creating any substitute prompts.
    (version_root / "ui_versions.json").write_text('{"versions": {}}', encoding="utf-8")
    # Make the conventional snapshot location unavailable, forcing run-path resolution.
    (version_root / "artifacts/versions/v1/system_prompt.md").unlink()
    runs, _ = read_runs(version_root)
    assert resolve_snapshot("v1", version_root, runs[0]).hashes == snapshot.hashes
    with pytest.raises(ValueError, match="Đường dẫn snapshot"):
        ui_data.local_path(version_root, "../secrets.md", (".md",))


class EchoProvider:
    default_model = "fake-model"

    def __init__(self, responses=None):
        self.requests = []
        self.responses = iter(responses) if responses else None

    def complete(self, messages, tools=None, **kwargs):
        self.requests.append(list(messages))
        if self.responses:
            return next(self.responses)
        return ModelResponse(text="Câu trả lời thử nghiệm.", raw={"model_version": "actual-test-model"})


@pytest.fixture
def ui_app(version_root, tmp_path, monkeypatch):
    AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
    monkeypatch.setattr(ui_data, "ROOT", version_root)
    monkeypatch.setenv("GEMINI_API_KEY", "fake-gemini-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-openrouter-key")
    sessions = []

    def factory(**kwargs):
        session = DemoSession(**kwargs, provider=EchoProvider(), transcripts_dir=tmp_path / "transcripts")
        sessions.append(session)
        return session

    monkeypatch.setattr(ui_session, "DemoSession", factory)
    app = AppTest.from_file(str(APP_PATH)).run(timeout=20)
    assert not app.exception
    return app, sessions


def test_ui_preserves_version_histories_and_uses_actual_snapshots(ui_app):
    app, sessions = ui_app
    app.button(key="example_policy").click().run()
    assert not app.exception
    first = sessions[-1]
    assert first.provider.requests[0][0]["content"] == "Prompt riêng của v0."
    assert first.transcript["actual_model"] == "actual-test-model"
    app.selectbox(key="chat_version").select("v2").run()
    app.chat_input[0].set_value("Câu hỏi cho v2").run()
    second = sessions[-1]
    assert second.provider.requests[0][0]["content"] == "Prompt riêng của v2."
    assert first.path != second.path
    app.selectbox(key="chat_version").select("v0").run()
    assert not app.exception
    assert app.session_state["version_sessions"].sessions["v0"] is first
    assert len(app.chat_message) == 2
    app.chat_input[0].set_value("Tiếp tục v0").run()
    assert len(first.transcript["turns"]) == 2
    assert "trích dẫn" in first.provider.requests[1][1]["content"]
    app.button(key="new_conversation").click().run()
    assert not app.exception
    assert "v0" not in app.session_state["version_sessions"].sessions
    assert app.session_state["version_sessions"].sessions["v2"] is second
    app.selectbox(key="chat_version").select("v2").run()
    assert len(app.chat_message) == 2 and second.path.exists()


def test_ui_provider_and_model_changes_start_new_sessions(ui_app):
    app, sessions = ui_app
    app.chat_input[0].set_value("Gemini chat").run()
    first = sessions[-1]
    app.selectbox(key="provider_v0").select("openrouter").run()
    assert not app.exception
    assert len(app.chat_message) == 0
    app.chat_input[0].set_value("OpenRouter chat").run()
    second = sessions[-1]
    assert second is not first and second.provider_name == "openrouter"
    assert len(second.provider.requests[0]) == 2
    app.text_input(key="model_v0_openrouter").input("custom/model").run()
    assert len(app.chat_message) == 0
    app.chat_input[0].set_value("Custom model chat").run()
    third = sessions[-1]
    assert third.model == "custom/model" and third is not second
    app.selectbox(key="chat_version").select("v2").run()
    app.selectbox(key="chat_version").select("v0").run()
    assert app.selectbox(key="provider_v0").value == "openrouter"
    assert app.text_input(key="model_v0_openrouter").value == "custom/model"
    assert app.session_state["version_sessions"].sessions["v0"] is third


def test_ui_renders_real_metrics_and_blocks_mismatched_snapshot(ui_app, version_root):
    app, _ = ui_app
    write_run(version_root, "v0")
    app.run()
    assert not app.exception
    table = app.dataframe[0].value
    assert table.iloc[0]["Pass"] == "50.00%"
    assert table.iloc[0]["Arguments"] == "0.00%"
    assert table.iloc[1]["Run JSON"] == "Chưa có run"
    app.checkbox(key="show_run_sources").check().run()
    assert not app.exception
    (version_root / "artifacts/versions/v0/system_prompt.md").write_text("Wrong snapshot", encoding="utf-8")
    app.run()
    assert app.chat_input[0].disabled
    assert any("không khớp prompt_hash" in item.value for item in app.warning)


def test_ui_missing_key_is_visible_and_prevents_api_request(ui_app, monkeypatch):
    app, sessions = ui_app
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    app.run()
    assert app.chat_input[0].disabled
    assert any("GEMINI_API_KEY" in item.value for item in app.error)
    assert not sessions


def test_ui_reports_ollama_not_running(ui_app, monkeypatch):
    app, _ = ui_app
    def disconnected(*args, **kwargs):
        raise requests.ConnectionError("Connection refused")
    monkeypatch.setattr(ui_session.requests, "get", disconnected)
    app.selectbox(key="provider_v0").select("ollama").run()
    app.button(key="check_ollama").click().run()
    assert not app.exception
    assert any("ollama serve" in item.value for item in app.error)


@pytest.mark.parametrize("tool", ["policy", "papers", "paper_text"])
def test_bonus_buttons_submit_real_requests_to_agent(ui_app, tool):
    app, sessions = ui_app
    app.button(key=f"example_{tool}").click().run()
    assert not app.exception and len(sessions) == 1
    assert len(sessions[0].provider.requests) == 1
    assert sessions[0].transcript["turns"][0]["user"]


@pytest.mark.parametrize("action", ["confirm_send", "cancel_send", "new_conversation"])
def test_ui_send_requires_button_and_never_exports_token(ui_app, tmp_path, monkeypatch, action):
    app, sessions = ui_app
    token = "123456789:abcdefghijklmnopqrstuvwxyz_123456789"
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", token)
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "fake-channel")
    calls = []

    def sender(**kwargs):
        calls.append(kwargs)
        return {"status": "sent", "message": "Token was " + token}

    monkeypatch.setattr(ui_session, "send_telegram", sender)
    monkeypatch.setitem(ui_session.TOOL_FUNCTIONS, "send", sender)

    def factory(**kwargs):
        provider = EchoProvider([ModelResponse(tool_calls=[
            ToolCall("send", {"text": "Bản nháp " + token, "confirmed": True})])])
        session = DemoSession(**kwargs, provider=provider, transcripts_dir=tmp_path / "send")
        sessions.append(session)
        return session

    monkeypatch.setattr(ui_session, "DemoSession", factory)
    app.button(key="example_send").click().run()
    assert not app.exception and calls == []
    session = sessions[-1]
    assert session.pending_send is not None
    visible = " ".join(str(item.value) for kind in ("code", "markdown", "json", "caption") for item in app.get(kind))
    assert token not in visible and token not in session.export_json()
    app.selectbox(key="chat_version").select("v2").run()
    app.selectbox(key="chat_version").select("v0").run()
    assert calls == [] and session.pending_send is not None
    app.button(key=action).click().run()
    assert not app.exception
    assert session.pending_send is None
    assert len(calls) == (1 if action == "confirm_send" else 0)
    if calls:
        assert calls[0] == {"text": "Bản nháp [REDACTED]", "confirmed": True}
    assert token not in session.path.read_text(encoding="utf-8")
    assert token not in session.export_json()
    app.run()
    assert len(calls) == (1 if action == "confirm_send" else 0)


def test_provider_errors_are_actionable(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert "GEMINI_API_KEY" in provider_problem("gemini")

    def disconnected(*args, **kwargs):
        raise requests.ConnectionError("Connection refused")

    monkeypatch.setattr(ui_session.requests, "get", disconnected)
    assert "ollama serve" in provider_problem("ollama", probe_ollama=True)


def test_compare_sources_inventory_updates_when_team_registers_it():
    rows = tool_inventory([], {})
    assert next(row for row in rows if row["Tool"] == "compare_sources")["Trạng thái"] != "Sẵn sàng"
    rows = tool_inventory([{"name": "compare_sources"}], {"compare_sources": object()})
    assert next(row for row in rows if row["Tool"] == "compare_sources")["Trạng thái"] == "Sẵn sàng"


def test_configuration_change_cancels_only_that_versions_pending_draft(version_root, tmp_path):
    store = VersionSessions()
    for version in ("v0", "v2"):
        session = DemoSession(version=version, snapshot=resolve_snapshot(version, version_root),
                              provider=EchoProvider([ModelResponse(tool_calls=[ToolCall("send", {"text": version})])]),
                              transcripts_dir=tmp_path / "drafts")
        session.submit("Soạn bản nháp")
        store.sessions[version] = session
    old = store.sessions["v0"]
    assert store.select("v0", "openrouter", "other-model", old.snapshot) is None
    assert old.transcript["turns"][0]["ui_action_gate"]["decision_reason"] == "configuration_changed"
    assert store.sessions["v2"].pending_send is not None
