"""Run with: python -m streamlit run app.py"""
from __future__ import annotations

import os

import streamlit as st

from providers import make_provider
from ui_session import DemoSession, public_data

st.set_page_config(page_title="Research Desk · Agent Demo", page_icon="🔎", layout="wide")

st.markdown("""
<style>
.block-container {max-width: 1040px; padding-top: 2.4rem;}
[data-testid="stSidebar"] {background: #f3f6fb;}
h1 {letter-spacing: -0.045em;}
.eyebrow {color: #3266c9; font-size: .75rem; font-weight: 750; letter-spacing: .18em;}
.intro {color: #64748b; max-width: 680px; font-size: 1.05rem; line-height: 1.65;}
</style>
""", unsafe_allow_html=True)

PROVIDERS = ["gemini", "openrouter", "openai", "anthropic", "ollama"]
EXAMPLES = [
    ("Tìm tin AI", "Tìm 3 tin tức AI nổi bật hôm nay, kèm liên kết nguồn."),
    ("Đọc bài đăng", "Lấy 3 bài đăng mới nhất của tài khoản @sama trên Twitter/X."),
    ("Thử hỏi lại", "Tóm tắt bài viết này giúp tôi."),
]


def render_turn(turn: dict) -> None:
    with st.chat_message("user"):
        st.markdown(turn["user"])
    with st.chat_message("assistant", avatar="🔎"):
        st.markdown(turn.get("assistant_text") or "Agent chưa trả về nội dung.")
        if turn.get("status") == "max_tool_rounds":
            st.warning("Agent đã chạm giới hạn 4 vòng gọi tool. Bạn có thể thu hẹp yêu cầu và thử lại.")
        errors = [event for event in turn.get("tool_events", [])
                  if isinstance(event.get("result"), dict) and event["result"].get("error")]
        if turn.get("error") or errors:
            st.error("Một dịch vụ chưa xử lý được yêu cầu. Kiểm tra chi tiết và thử lại sau.")
        if turn.get("rounds") or turn.get("ui_action_gate") or turn.get("error"):
            names = [event["tool"] for event in turn.get("tool_events", [])]
            label = " → ".join(names) if names else "Chi tiết xử lý"
            with st.expander(label):
                st.json(public_data({
                    "status": turn["status"],
                    "rounds": turn.get("rounds", []),
                    "ui_action_gate": turn.get("ui_action_gate"),
                    "tool_events": turn.get("tool_events", []),
                    "error": turn.get("error"),
                }))


session: DemoSession | None = st.session_state.get("demo_session")
with st.sidebar:
    st.markdown("### 🔎 Research Desk")
    st.caption("Tìm thông tin · Đọc nguồn · Tạo bản tin")
    if st.button("＋ Cuộc trò chuyện mới", use_container_width=True):
        st.session_state.pop("demo_session", None)
        st.rerun()
    with st.expander("Cấu hình demo", expanded=session is None):
        provider_name = st.selectbox("Provider", PROVIDERS, index=0, disabled=session is not None)
        default_model = make_provider(provider_name).default_model
        model = st.text_input("Model (để trống dùng mặc định)", placeholder=default_model, disabled=session is not None)
        version = st.text_input("Nhãn phiên bản prompt/tools", value="v0", disabled=session is not None)
        st.caption("Chọn nhãn đúng với bản prompt đang thử. Nhãn v3 không tự tối ưu prompt.")
    st.divider()
    st.caption("Công cụ của agent")
    st.markdown("**Web:** lookup, fetch\n\n**Twitter/X:** timeline, social_search\n\n"
                "**Nghiên cứu:** policy, papers, paper_text\n\n**Hội thoại:** clarify, format, send")
    telegram_ready = all(os.getenv(name) for name in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"))
    st.caption("Telegram: " + ("đã cấu hình" if telegram_ready else "chưa cấu hình · vẫn có thể thử bản nháp"))
    if session is not None:
        st.divider()
        st.caption(f"{session.transcript['provider']} · {session.model}")
        st.caption(f"{len(session.transcript['turns'])} lượt · tự lưu transcript JSON")
        st.download_button("↓ Tải transcript JSON", session.export_json(),
                           file_name=session.path.name, mime="application/json", use_container_width=True)
        with st.expander("Bằng chứng phiên bản"):
            st.code(session.transcript["artifact_version"], language="text")
            st.caption(f"File: transcripts/{session.path.name}")

st.markdown('<div class="eyebrow">LIVE RESEARCH / TOOL-POWERED AGENT</div>', unsafe_allow_html=True)
st.title("Hỏi, tìm, kiểm chứng.")
st.markdown('<p class="intro">Một bàn nghiên cứu nhỏ cho câu hỏi lớn. Tìm trên web, đọc nguồn và theo dõi từng công cụ agent sử dụng.</p>', unsafe_allow_html=True)

prompt = None
if session is None or not session.transcript["turns"]:
    st.write("")
    for column, (label, text) in zip(st.columns(3), EXAMPLES):
        if column.button(label, use_container_width=True, help=text):
            prompt = text
    st.info("Chọn câu hỏi mẫu hoặc nhập yêu cầu bên dưới. Nếu agent hỏi lại, hãy trả lời ở lượt tiếp theo.")
    st.caption("Demo sử dụng prompt của bài lab; kết quả có thể có lỗi. Bạn có thể xem lời gọi tool và tải transcript để đánh giá.")
else:
    for turn in session.transcript["turns"]:
        render_turn(turn)

if session is not None and session.pending_send is not None:
    st.subheader("Xem lại trước khi gửi Telegram")
    st.markdown(public_data(session.pending_send["text"]) or "Bản nháp trống.")
    if not telegram_ready:
        st.info("Máy chủ chưa cấu hình Telegram. Bạn có thể hủy bản nháp để tiếp tục chat.")
    confirm_column, cancel_column = st.columns(2)
    confirmed = confirm_column.button("Xác nhận gửi Telegram", type="primary", disabled=not telegram_ready, use_container_width=True)
    cancelled = cancel_column.button("Hủy gửi", use_container_width=True)
    if confirmed or cancelled:
        try:
            session.resolve_send(confirmed=confirmed)
            st.rerun()
        except Exception as exc:
            st.error(public_data(str(exc)))

typed = st.chat_input("Bạn muốn tìm hiểu điều gì?", max_chars=4000,
                      disabled=session is not None and session.pending_send is not None)
prompt = typed or prompt
if prompt:
    try:
        if session is None:
            session = DemoSession(provider_name=provider_name, model=model.strip() or None, version=version.strip() or "v0")
            st.session_state.demo_session = session
        with st.spinner("Agent đang tìm thông tin và xử lý yêu cầu…"):
            session.submit(prompt)
        st.rerun()
    except Exception as exc:
        st.error(public_data(f"Không thể xử lý hoặc lưu phiên chat: {exc}"))
