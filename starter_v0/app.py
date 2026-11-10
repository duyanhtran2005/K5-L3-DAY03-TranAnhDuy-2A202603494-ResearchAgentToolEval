"""Versioned demo. Run: python -X utf8 -m streamlit run app.py"""
from __future__ import annotations
import os
import streamlit as st
from providers import make_provider
from tools import TOOL_FUNCTIONS
from ui_data import ROOT, CHAT_VERSIONS, comparison_rows, latest_runs, read_runs, resolve_snapshot, tool_inventory
from ui_session import DemoSession, VersionSessions, friendly_error, provider_problem, public_data

st.set_page_config(page_title="Research Desk · Agent Demo", page_icon="🔎", layout="wide")
st.markdown("""
<style>
.block-container {max-width: 1180px; padding-top: 2.2rem;}
h1 {letter-spacing: -0.045em;}
.eyebrow {color: #3266c9; font-size: .75rem; font-weight: 750; letter-spacing: .18em;}
.intro {color: #64748b; font-size: 1.05rem; line-height: 1.65;}
</style>
""", unsafe_allow_html=True)

PROVIDERS = ["gemini", "openrouter", "ollama", "openai", "anthropic"]
EXAMPLES = [
    ("lookup", "Tin AI", "Tìm 3 tin tức AI nổi bật hôm nay, kèm liên kết nguồn."),
    ("policy", "Chính sách nội bộ", "Tìm chính sách nội bộ về trích dẫn nguồn khi viết bản tin."),
    ("papers", "Tìm paper arXiv", "Tìm 3 bài báo arXiv về đánh giá AI agent."),
    ("paper_text", "Đọc một paper", "Đọc 2 trang đầu của bài arXiv 1706.03762 và tóm tắt các ý chính."),
    ("compare_sources", "So sánh nguồn", 'Dùng compare_sources để kiểm tra URL trùng trong các nguồn: [{"url":"https://example.com/report#intro"},{"url":"https://example.com/report#results"},{"url":"https://other.org/post"}].'),
    ("send", "Bản nháp Telegram", 'Gửi bản tin "Đây là bản tin demo của nhóm" lên Telegram.'),
]


def render_turn(turn: dict, provider_name: str) -> None:
    with st.chat_message("user"):
        st.markdown(turn["user"])
    with st.chat_message("assistant", avatar="🔎"):
        st.markdown(turn.get("assistant_text") or "Agent chưa trả về nội dung.")
        if turn.get("actual_models"):
            st.caption("Model phản hồi: " + ", ".join(turn["actual_models"]))
        if turn.get("status") == "max_tool_rounds":
            st.warning("Agent đã chạm giới hạn 4 vòng gọi tool. Hãy thu hẹp yêu cầu hoặc xem chi tiết bên dưới.")
        errors = [str(event["result"].get("message") or event["result"]["error"])
                  for event in turn.get("tool_events", [])
                  if isinstance(event.get("result"), dict) and event["result"].get("error")]
        if turn.get("error") or errors:
            st.error(friendly_error(str(turn.get("error") or errors[0]), provider_name))
        names = [event["tool"] for event in turn.get("tool_events", [])]
        with st.expander("Chi tiết xử lý" + (" · " + " → ".join(names) if names else "")):
            st.json(public_data({
                "status": turn["status"], "actual_models": turn.get("actual_models", []),
                "rounds": turn.get("rounds", []), "tool_events": turn.get("tool_events", []),
                "ui_action_gate": turn.get("ui_action_gate"), "error": turn.get("error"),
            }))


st.markdown('<div class="eyebrow">RESEARCH DESK / VERSION LAB</div>', unsafe_allow_html=True)
st.title("Hỏi, tìm, kiểm chứng.")
st.markdown('<p class="intro">So sánh kết quả đánh giá, trò chuyện với từng phiên bản và xem bằng chứng sau mỗi câu trả lời.</p>', unsafe_allow_html=True)

runs, run_errors = read_runs(ROOT)
cohorts = sorted({run.cohort for run in runs}, key=lambda value: (value[0] != "base", value))
with st.expander("So sánh đánh giá v0–v3", expanded=True):
    cohort = st.selectbox("Bộ đánh giá · provider · model · dataset", cohorts,
                          format_func=lambda value: " · ".join(value), key="eval_cohort") if cohorts else None
    selected_runs = latest_runs(runs, cohort)
    st.dataframe(comparison_rows(selected_runs), hide_index=True, use_container_width=True)
    st.caption("Lấy run mới nhất của mỗi version trong cùng suite/provider/model/dataset. Pass = case_accuracy; ô — là chưa có phép đo.")
    if not runs:
        st.info("Chưa có run JSON trong runs/. Bảng sẽ tự cập nhật khi nhóm bổ sung kết quả v0–v3.")
    if run_errors:
        st.warning("Một số run JSON chưa đọc được: " + "; ".join(run_errors))
    if selected_runs and st.checkbox("Hiện nguồn số liệu", key="show_run_sources"):
        st.json(public_data({version: {"file": str(run.path), "generated_at": run.data.get("generated_at"),
                                      "summary": run.data["summary"], "prompt_hash": run.data.get("prompt_hash"),
                                      "tools_hash": run.data.get("tools_hash")}
                             for version, run in selected_runs.items()}))

if "version_sessions" not in st.session_state:
    st.session_state.version_sessions = VersionSessions()
store: VersionSessions = st.session_state.version_sessions

with st.sidebar:
    st.markdown("### 🔎 Research Desk")
    version = st.selectbox("Phiên bản chat", CHAT_VERSIONS, key="chat_version",
                           format_func=lambda value: "group-v1 · tool mới (10/10)" if value == "group-v1" else value)
    snapshot, snapshot_error = None, None
    try:
        snapshot = resolve_snapshot(version, ROOT, selected_runs.get(version))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        snapshot_error = str(exc)
    preferences = store.preferences.get(version, {"provider": "gemini", "model": ""})
    provider_name = st.selectbox("Provider", PROVIDERS, index=PROVIDERS.index(preferences["provider"]),
                                key=f"provider_{version}")
    default_model = make_provider(provider_name).default_model
    saved_model = preferences["model"] if preferences["provider"] == provider_name else ""
    model_input = st.text_input("Model (để trống dùng mặc định)", value=saved_model,
                               placeholder=default_model, key=f"model_{version}_{provider_name}")
    effective_model = model_input.strip() or default_model
    store.preferences[version] = {"provider": provider_name, "model": model_input}
    had_session = version in store.sessions
    session = store.select(version, provider_name, effective_model, snapshot)
    if had_session and session is None:
        st.info("Đã bắt đầu phiên mới vì provider, model hoặc snapshot thay đổi.")
    st.caption(f"Model gửi tới provider: {effective_model}")
    if session and session.transcript.get("actual_model"):
        st.caption(f"Model phản hồi thực tế: {session.transcript['actual_model']}")
    configuration_error = provider_problem(provider_name)
    if configuration_error:
        st.error(configuration_error)
    if provider_name == "ollama" and st.button("Kiểm tra Ollama", key="check_ollama"):
        problem = provider_problem("ollama", probe_ollama=True)
        if problem:
            st.error(problem)
        else:
            st.success("Đã kết nối được Ollama.")
    if snapshot_error:
        st.warning(public_data(snapshot_error))
    elif snapshot:
        st.caption(f"Đang dùng snapshot {version} · {snapshot.hashes[0][:12]}")
    if st.button("＋ Cuộc trò chuyện mới", key="new_conversation", use_container_width=True):
        store.reset(version)
        st.rerun()
    st.caption("Lịch sử được giữ riêng theo version trong phiên trình duyệt này. Đổi provider/model sẽ bắt đầu cuộc trò chuyện mới cho version đang chọn.")
    if session:
        st.divider()
        st.caption(f"{len(session.transcript['turns'])} lượt · {version}")
        st.download_button(f"↓ Tải transcript {version} (JSON)", session.export_json(),
                           file_name=session.path.name, mime="application/json", key=f"download_{version}",
                           use_container_width=True)
    if snapshot:
        with st.expander("Snapshot đang sử dụng"):
            st.json(snapshot.evidence)
            st.caption(snapshot.prompt_source)
            st.code(public_data(snapshot.prompt), language="text")

declarations = snapshot.declarations if snapshot else []
inventory = tool_inventory(declarations, TOOL_FUNCTIONS, ROOT)
with st.expander("Công cụ và mô tả"):
    st.dataframe(inventory, hide_index=True, use_container_width=True)
    st.caption("Tool sẵn sàng khi có khai báo trong snapshot và implementation. Chọn group-v1 để dùng compare_sources; snapshot v0–v3 giữ nguyên theo run gốc.")

st.subheader(f"Cuộc trò chuyện · {version}")
can_chat = snapshot is not None and configuration_error is None
pending = session is not None and session.pending_send is not None
available = {row["Tool"] for row in inventory if row["Trạng thái"] == "Sẵn sàng"}
prompt = None
with st.expander("Thử nhanh các công cụ", expanded=session is None or not session.transcript["turns"]):
    columns = st.columns(3)
    for index, (tool, label, query) in enumerate(EXAMPLES):
        if columns[index % 3].button(label, key=f"example_{tool}", help=query, use_container_width=True,
                                     disabled=not can_chat or pending or tool not in available):
            prompt = query
    st.caption("Mỗi nút gửi một yêu cầu tới agent. Mở chi tiết để kiểm tra model có chọn đúng tool không.")

if session:
    for turn in session.transcript["turns"]:
        render_turn(turn, session.provider_name)
else:
    st.info("Nhập câu hỏi hoặc chọn mẫu bên trên. Bạn có thể chuyển phiên bản rồi quay lại để tiếp tục lịch sử cũ.")

if pending:
    st.subheader("Bản nháp Telegram")
    draft = session.pending_send["text"]
    st.code(public_data(draft) if isinstance(draft, str) else "Bản nháp không hợp lệ.", language=None)
    telegram_ready = all(os.getenv(name) for name in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"))
    if not telegram_ready:
        st.info("Máy chủ chưa cấu hình Telegram. Bạn có thể xem bản nháp và hủy gửi.")
    confirm_column, cancel_column = st.columns(2)
    confirmed = confirm_column.button("Xác nhận gửi Telegram", type="primary", key="confirm_send",
                                       disabled=not can_chat or not telegram_ready or not isinstance(draft, str) or not draft.strip(),
                                       use_container_width=True)
    cancelled = cancel_column.button("Hủy gửi", key="cancel_send", use_container_width=True)
    if confirmed or cancelled:
        try:
            with st.spinner("Đang xử lý bản nháp…"):
                session.resolve_send(confirmed=confirmed)
            st.rerun()
        except Exception as exc:
            st.error(public_data(str(exc)))

typed = st.chat_input("Bạn muốn tìm hiểu điều gì?", max_chars=4000, disabled=not can_chat or pending)
prompt = typed or prompt
if prompt and can_chat and not pending:
    try:
        if session is None:
            session = DemoSession(provider_name=provider_name, model=effective_model,
                                  version=version, snapshot=snapshot)
            store.sessions[version] = session
        with st.spinner("Agent đang tìm thông tin và xử lý yêu cầu…"):
            session.submit(prompt)
        st.rerun()
    except Exception as exc:
        st.error(public_data(f"Không thể xử lý hoặc lưu phiên chat: {exc}"))
