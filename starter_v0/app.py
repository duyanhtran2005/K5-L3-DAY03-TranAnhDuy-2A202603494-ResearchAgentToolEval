"""Simple live demo: python -m streamlit run app.py"""
import json
import hashlib
from pathlib import Path

import streamlit as st

from chat import run_model_tool_loop
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools

ROOT = Path(__file__).parent
st.set_page_config(page_title="Research Agent Demo", page_icon="🔎")
st.title("🔎 Research Agent Demo")
st.caption("Tìm web, đọc URL, tìm bài đăng và xem agent đã gọi tool nào.")

with st.expander("Kết quả base eval: v0 → v3", expanded=True):
    rows = []
    for version in ("v0", "v1", "v2", "v3"):
        files = sorted((ROOT / "runs").glob(f"{version}_B_base_openrouter_*.json"))
        if files:
            summary = json.loads(files[-1].read_text(encoding="utf-8"))["summary"]
            rows.append({
                "Version": version,
                "Pass": f"{summary['passed_cases']}/{summary['measured_cases']}",
                "Routing": f"{summary['tool_routing_accuracy']:.0%}",
                "Arguments": f"{summary['argument_accuracy']:.0%}",
                "Multi-turn": f"{summary['multiturn_accuracy']:.1%}",
            })
    st.dataframe(rows, hide_index=True, width="stretch")
    st.caption("v2 đạt điểm cao nhất (19/20). Bảng là kết quả eval đã lưu; chat live có thể khác giữa các lần chạy.")

selected_version = st.selectbox("Chọn prompt để chat", ("v0", "v1", "v2", "v3"), index=2)
prompt_path = ROOT / "artifacts" / "prompts" / f"{selected_version}.md"
tools_path = ROOT / "artifacts" / "prompts" / "tools_v0-v3.yaml"
run_files = sorted((ROOT / "runs").glob(f"{selected_version}_B_base_openrouter_*.json"))
run_info = json.loads(run_files[-1].read_text(encoding="utf-8"))
if (hashlib.sha256(prompt_path.read_bytes()).hexdigest() != run_info["prompt_hash"]
        or hashlib.sha256(tools_path.read_bytes()).hexdigest() != run_info["tools_hash"]):
    st.error("Prompt hoặc tool snapshot không khớp run JSON của phiên bản này.")
    st.stop()
st.caption(f"Prompt và tool declaration {selected_version} đã khớp hash run JSON. Tool gửi Telegram bị tắt trong UI demo.")

if "history" not in st.session_state:
    st.session_state.history = []
    st.session_state.turns = []
if st.session_state.get("active_version") != selected_version:
    st.session_state.active_version = selected_version
    st.session_state.history = []
    st.session_state.turns = []

if st.button("Cuộc trò chuyện mới"):
    st.session_state.history = []
    st.session_state.turns = []
    st.rerun()

for turn in st.session_state.turns:
    with st.chat_message("user"):
        st.write(turn["user"])
    with st.chat_message("assistant"):
        st.write(turn["answer"])
        with st.expander("Tool đã gọi"):
            st.json(turn["tools"])

if question := st.chat_input("Ví dụ: Tóm tắt bài viết này giúp tôi"):
    prompt = prompt_path.read_text(encoding="utf-8")
    declarations = load_tool_declarations(tools_path)
    # The public demo only runs read/control tools; send requires a separate confirmation flow.
    tools = to_openai_tools([tool for tool in declarations if tool["name"] != "send"])
    messages = [{"role": "system", "content": prompt}, *st.session_state.history,
                {"role": "user", "content": question}]
    with st.spinner("Agent đang xử lý..."):
        try:
            result = run_model_tool_loop(
                provider=make_provider("openrouter"), messages=messages,
                tools=tools, model=None, max_tool_rounds=4,
            )
            answer = result["assistant_text"] or "Agent chưa trả lời."
            events = result["tool_events"]
        except Exception as exc:
            answer = f"Lỗi: {type(exc).__name__}: {exc}"
            events = []
    st.session_state.turns.append({"user": question, "answer": answer, "tools": events})
    st.session_state.history.extend([
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer},
    ])
    st.rerun()
