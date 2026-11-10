# Day 03 Lab v2 Report — Research Agent

## Team

- Team:
- Members:
- Provider/model: Gemini / `gemini-3.5-flash`

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research Agent là trợ lý AI hỗ trợ tìm thông tin trên web và Twitter/X, đọc nội dung từ URL, và tổng hợp dữ liệu thành bản tin có liên kết nguồn. Bộ công cụ còn hỗ trợ tra cứu chính sách nội bộ, tìm và đọc bài báo arXiv, cùng chức năng gửi bản tin lên Telegram khi được người dùng xác nhận.

**Trạng thái hiện tại:** đã có UI Streamlit và chạy 4 lượt kiểm tra Step 5 bằng Gemini thật, lưu transcript JSON. Agent đọc được URL và tạo bản tóm tắt; một số lượt gặp lỗi Gemini 503 và prompt gốc còn tự đoán URL khi thiếu thông tin (chi tiết B4). Telegram chưa cấu hình; UI hỗ trợ xem và hủy bản nháp trước khi gửi.

**Link dùng thử (deploy):**

[Mở Research Desk Demo](https://partnership-vacation-spouse-batman.trycloudflare.com)

UI Streamlit chạy qua Cloudflare Quick Tunnel; đã kiểm tra trang chủ và endpoint health đều trả HTTP 200. Link tạm thời, chỉ hoạt động khi máy demo cùng Streamlit và cloudflared còn chạy. Địa chỉ local: http://localhost:8501. Hướng dẫn khởi động lại: `UI-README.md`.

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| `clarify` | Hỏi lại người dùng để bổ sung thông tin hoặc xác nhận yêu cầu. | Không |
| `timeline` | Lấy các bài đăng gần đây của một tài khoản Twitter/X. | Không |
| `social_search` | Tìm bài đăng Twitter/X theo từ khóa, ưu tiên mới nhất hoặc phổ biến. | Không |
| `lookup` | Tìm thông tin trên web, hỗ trợ tìm tin tức theo khoảng thời gian. | Không |
| `fetch` | Đọc nội dung của một URL để phục vụ việc tóm tắt và nghiên cứu. | Không |
| `format` | Trình bày các dữ liệu đã có thành bản tin Markdown theo mẫu. | Không |
| `send` | Gửi văn bản lên kênh Telegram đã cấu hình khi `confirmed=true`. | Không |
| `policy` | Tìm thông tin trong bộ tài liệu chính sách nội bộ của bài lab. | Không |
| `papers` | Tìm bài báo khoa học trên arXiv theo chủ đề. | Không |
| `paper_text` | Tải PDF arXiv và trích xuất văn bản theo giới hạn trang, ký tự. | Không |

Danh sách trên là các tool có sẵn, đã được khai báo và đăng ký trong bộ khung. Nhóm chưa bổ sung tool mới.

## A3. Câu hỏi mẫu để thử

1. **Tìm tin trên web:** “Tìm 5 tin tức AI nổi bật hôm nay, kèm liên kết nguồn.”
2. **Đọc bài đăng theo tài khoản:** “Lấy 5 bài đăng mới nhất của tài khoản @sama trên Twitter/X.”
3. **Tìm bài đăng theo chủ đề:** “Tìm 5 bài đăng phổ biến nhất về AI agents trên Twitter/X.”
4. **Đọc URL:** “Đọc và tóm tắt trang https://www.python.org/about/ thành 3 ý chính.”
5. **Thử tình huống thiếu thông tin:** “Lấy 5 bài đăng mới nhất giúp tôi.” Sau khi agent hỏi tài khoản, trả lời: “Tài khoản @sama.” Hành vi mong đợi là hỏi lại trước khi lấy dữ liệu.

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline |  |  |  |  |
| v1 |  |  |  |  |  |
| v2 |  |  |  |  |  |
| v3 |  |  |  |  |  |

## B2. Failure Analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
|  |  |  |  |  |

## B3. Team Eval Cases

List the 10 cases added to `data/eval_group.json` (5 single turn + 5 multi turn).

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
|  |  |  |  |

## B4. Live Chat Evidence

Use `transcripts/*.transcript.json`.

Kiểm tra qua adapter hội thoại của UI, dùng lại vòng xử lý của `chat.py`, với Gemini / `gemini-3.5-flash`. Bằng chứng: `transcripts/v0-step5-demo_gemini_ui_8c8e838bd3eb409681c76a11fc63c0d6.transcript.json`. Artifact: `v0-step5-demo+peb1c8179815b+t5b22a2476d41` (prompt/tools gốc, chưa phải bản tối ưu v3).

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | Tìm 2 tin tức AI nổi bật hôm nay, kèm nguồn. | `lookup` | `v0-step5-demo`, lượt 1 | Tool trả 5 kết quả; Gemini trả 503 khi tạo câu trả lời tiếp theo. Chưa hoàn thành yêu cầu. |
| 2 | Tóm tắt bài viết này giúp tôi. | `fetch` với URL OpenAI do model tự đoán | `v0-step5-demo`, lượt 2 | Sai hành vi khi thiếu URL: không hỏi lại; sau khi đọc trang thì Gemini trả 503. |
| 3 | URL bài viết là https://www.python.org/about/. | `fetch` → `format` | `v0-step5-demo`, lượt 3 | Đọc đúng URL và trả bản tóm tắt có liên kết nguồn. |
| 4 | Gửi bản tin “Đây là bản tin demo của nhóm” lên Telegram. | Model yêu cầu `send`; UI dừng trước khi thực thi | `v0-step5-demo`, lượt 4, `ui_action_gate` | Hiện bản nháp rồi hủy trong lượt kiểm tra; không gửi tin. Cơ chế xác nhận thuộc UI, không chứng minh prompt đã biết hỏi xác nhận. |

## B5. Bonus Evidence

Only fill if your team did bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) |  |  |  |
| arXiv/company policy |  |  |  |
| UI | `app.py`, `ui_session.py`, `UI-README.md`; link Phần A | Chat nhiều lượt, xem tool, lưu/tải transcript; 8 test UI/session offline đạt; public HTTP 200 | Mỗi người có phiên riêng; gửi Telegram phải bấm xác nhận; link tunnel tồn tại theo tiến trình demo. |
| Tool unit tests (`tests/`) | `pytest` output |  |  |

Tool unit tests: số test đã viết, số bug tìm được trong tool có sẵn (nếu có), và một ví dụ lỗi mà unit test bắt được nhưng eval không bắt được.

## B6. Reflection

- Which fixes belonged in `system_prompt.md`?
- Which fixes belonged in `tools.yaml`?
- Which failure needed manual review instead of automatic grading?
- What would you improve next?

## B7. Small Local Model Challenge (bonus)

Only fill if your team did the local model challenge.

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v3 | (cloud) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v4-local |  |  |  |  |  |  |  |
| v5-local |  |  |  |  |  |  |  |

Lỗi đặc thù của model nhỏ (đếm từ run JSON):

| Failure Pattern | Count | Example Case | Fix Tried | Helped? |
|---|---|---|---|---|
| wrong / hallucinated tool |  |  |  |  |
| invalid JSON args (`_invalid_json_arguments`) |  |  |  |  |
| no tool call / answered directly |  |  |  |  |
| missed `clarify` |  |  |  |  |
| repeated / unnecessary calls |  |  |  |  |

- Cái gì giúp model nhỏ gọi tool đúng hơn nhất? Bằng chứng?
- Bản prompt tối ưu cho local chạy trên model cloud thì sao?
- Khi nào nhóm sẽ chọn model local thay vì cloud cho agent này?
