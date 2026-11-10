"""Simple live demo: python -m streamlit run app.py"""
import json
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
    st.caption("v2 đạt điểm cao nhất (19/20). Chat bên dưới dùng prompt hiện tại trong artifacts/system_prompt.md (v3).")

if "history" not in st.session_state:
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
    prompt = (ROOT / "artifacts/system_prompt.md").read_text(encoding="utf-8")
    declarations = load_tool_declarations(ROOT / "artifacts/tools.yaml")
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
