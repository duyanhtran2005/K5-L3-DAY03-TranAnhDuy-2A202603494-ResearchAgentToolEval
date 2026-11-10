# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: TranAnhDuy-2A202603494
- Members: Trần Anh Duy, Trần Dương Trung Tính, Trương Lợi Vĩ, Bùi Thế Anh, Nguyễn Nhựt Linh.
- Provider/model: OpenRouter / `openai/gpt-4o-mini` cho các run base và group eval; Gemini được dùng trong một số transcript UI.

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

> 1–2 câu mô tả agent dùng để làm gì (cho team khác hiểu nhanh).

Research Desk tìm thông tin trên web và Twitter/X, đọc URL, tra chính sách nội bộ và bài báo arXiv, rồi trình bày kết quả kèm nguồn. Tool mới `compare_sources` loại URL trùng và thống kê hostname; có chức năng gửi Telegram trong UI nhưng thao tác cần người dùng xác nhận.

**Link dùng thử (deploy):**

> Dán link public để team khác mở thử ngay. Cách deploy nhanh bằng Cloudflare Tunnel xem README. Nếu deploy Vercel/Streamlit Cloud thì dán link đó.
> https://coupons-karen-scientific-helmet.trycloudflare.com 

## A2. Tool agent có

> Liệt kê các tool agent đang dùng (gồm tool mới nhóm tự thêm). Mỗi tool 1 dòng: tên + làm được gì.

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi lại khi thiếu thông tin hoặc cần xác nhận. | không |
| timeline | Lấy bài đăng gần đây của một tài khoản X. | không |
| social_search | Tìm bài đăng X theo từ khóa. | không |
| lookup | Tìm thông tin và tin tức trên web. | không |
| fetch | Đọc nội dung một URL cụ thể. | không |
| format | Trình bày dữ liệu đã có thành Markdown. | không |
| send | Gửi văn bản lên Telegram khi đã xác nhận. | không |
| policy | Tra cứu chính sách nội bộ. | không |
| papers | Tìm paper trên arXiv. | không |
| paper_text | Trích văn bản từ PDF arXiv. | không |
| compare_sources | Loại URL lặp và đếm nguồn theo hostname; không kiểm chứng độ tin cậy. | có |

## A3. Câu hỏi mẫu để thử

> 3–5 câu hỏi/yêu cầu mẫu để team khác tự thử agent ngay.

1. Tìm 3 tin tức AI hôm nay, kèm liên kết nguồn.
2. Lấy 5 bài đăng gần nhất của tài khoản @sama.
3. Đọc và tóm tắt https://www.python.org/about/ thành 3 ý.
4. Tìm 3 paper về AI literacy in higher education trên arXiv.
5. So sánh các URL `https://example.com/a#intro`, `https://example.com/a#results`, `https://other.org/b`: bỏ trùng và đếm hostname (chọn phiên chat `group-v1`).

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Đo hành vi starter. | — | 14/20 (70%) | `runs/v0_B_base_openrouter_20261110T101352845797.json` |
| v1 | `system_prompt.md` | Hướng dẫn hỏi lại khi thiếu tài khoản/URL. | 14/20 (70%) | 14/20 (70%); routing 75%→85% | `runs/v1_B_base_openrouter_20261110T103423082376.json` |
| v2 | `system_prompt.md` | Bỏ chỉ dẫn đoán, quy định rõ tham số của `clarify`. | 14/20 (70%) | 19/20 (95%) | `runs/v2_B_base_openrouter_20261110T104018502733.json` |
| v3 | `system_prompt.md` | Thêm quy tắc xác nhận gửi và bỏ ép xử lý một bước. | 19/20 (95%) | 16/20 (80%) | `runs/v3_B_base_openrouter_20261110T104309505202.json` |

Cả bốn run đều đo đủ 20 case, `provider_error_cases=0`. Hash và giả thuyết chi tiết nằm trong `artifacts/version_log.csv`. v2 đạt điểm base cao nhất; v3 giảm do hỏi xác nhận thừa và đổi nhầm tool ở một số case.

## B2. Failure Analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R08, R14 (v0) | out_of_scope | `send` | Dùng tool gửi cho yêu cầu toán/lập trình ngoài phạm vi. | Bỏ chỉ dẫn gửi vô điều kiện; v2/v3 PASS. |
| R10 (v0) | missing_info | `timeline(screenname="sama")` | Tự đoán tài khoản. | Hỏi lại bằng `clarify`; v2/v3 PASS. |
| R11 (v0) | missing_info | `fetch(url="https://www.example.com/article")` | Tự đoán URL. | Hỏi URL; v2/v3 PASS. |
| R12 (v0–v3) | wrong_boundary | v0–v2 gọi `send`; v3 gọi `clarify(response_type="text")` | v3 đã dừng gửi nhưng chưa hỏi xác nhận yes/no đúng kỳ vọng. | Cần chỉ rõ câu xác nhận và `response_type="yes_no"`; chưa có run base chứng minh đã sửa. |
| R13 (v0) | wrong_tool | `lookup(query="AI news")` thiếu `topic`, cùng `social_search` | Sai query/topic của tra cứu tin. | v2/v3 PASS; kiểm tra args trong run. |
| R04, R05 (v3) | wrong_tool | `clarify` | Hỏi xác nhận thừa dù URL/limit đã rõ. | Giới hạn xác nhận cho action `send`. |
| M06 (v3) | wrong_tool | `social_search` | Không chuyển sang `lookup` khi người dùng đổi yêu cầu. | Bổ sung quy tắc ưu tiên ý định mới nhất. |

## B3. Team Eval Cases

List the 10 cases added to `data/eval_group.json` (5 single turn + 5 multi turn).

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_policy_source_citation | Tra chính sách trích dẫn | `policy(source_citation, top_k=3)` | PASS |
| G02_papers_relevance | Tìm paper theo độ liên quan | `papers(max_results=5, sort_by=relevance)` | PASS |
| G03_paper_text_url | Đọc PDF arXiv | `paper_text` với URL, 3 trang, 6000 ký tự | PASS |
| G04_format_bullets | Trình bày item có sẵn | `format(template=bullets)` | PASS |
| G05_compare_sources_single | Route tới tool mới, bỏ URL trùng | `compare_sources(max_items=2)` | PASS |
| G06_policy_multiturn_scope | Đổi phạm vi qua nhiều lượt | `policy(data_privacy, top_k=2)` | PASS |
| G07_papers_multiturn_sort | Đổi cách sắp xếp paper | `papers(sort_by=lastUpdatedDate)` | PASS |
| G08_paper_text_multiturn_pages | Giữ URL, đổi giới hạn trang | `paper_text(max_pages=2, max_chars=4000)` | PASS |
| G09_format_multiturn_template | Giữ item, đổi template | `format(template=bullets)` | PASS |
| G10_compare_sources_multiturn_limit | Giữ URL, đổi giới hạn kết quả | `compare_sources(max_items=1)` | PASS |

Nguồn: `data/eval_group.json` và `runs/group-v1_B_group_openrouter_20261110T145407529922.json` (`10/10`, đủ 10 case, 0 lỗi provider). Prompt group được lưu tại `artifacts/system_prompt_group_v1.md`; đây là suite khác với base v0–v3.

## B4. Live Chat Evidence

Use `transcripts/*.transcript.json`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | Tìm 2 tin AI, kèm nguồn | `lookup` | `transcripts/v0-step5-demo_gemini_ui_8c8e838bd3eb409681c76a11fc63c0d6.transcript.json`, lượt 1 | Tool trả kết quả nhưng Gemini 503 khi tổng hợp; chưa hoàn tất. |
| 2 | “Tóm tắt bài viết này” khi chưa có URL | `fetch` với URL do model đoán | Cùng transcript, lượt 2, snapshot v0 | Sai boundary thiếu thông tin; Gemini 503 sau tool. |
| 3 | Bổ sung URL python.org/about | `fetch` → `format` | Cùng transcript, lượt 3 | Đọc đúng URL và trả tóm tắt. |
| 4 | Gửi bản tin lên Telegram | Model yêu cầu `send`; UI chặn trước khi thực thi | Cùng transcript, lượt 4 | Người dùng hủy bản nháp; không có bằng chứng đã gửi. |
| 5 | Tin OpenAI; sau đó hỏi bài đăng, bổ sung “OpenAI”, rồi yêu cầu gửi | `lookup`/`social_search`; không có `send` thực thi | `transcripts/v3_openrouter_20261110T112725623048.transcript.json`, lượt 1–4 | Có hội thoại OpenRouter v3; cần đọc tool events để đánh giá từng lời đáp, không coi là bằng chứng gửi Telegram. |

## B5. Bonus Evidence

Only fill if your team did bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | Transcript UI v0 ở B4, lượt 4 | UI tạo bản nháp và cho phép hủy trước khi gửi. | Chưa có transcript `status: sent`; không nhận bonus gửi thật. |
| arXiv/company policy | `tools/papers/`, `tools/paper_text/`, `tools/policy/`; run group-v1 | Route đúng trong eval nhóm. | Tool có sẵn trong starter, không tính tool mới. |
| UI | `app.py`, `ui_data.py`, `ui_session.py`, `UI-README.md`, `tests/test_ui_demo.py`, `tests/test_ui_versions.py` | So sánh v0–v3, chat theo snapshot và chọn provider/model; `group-v1` cho tool mới. | Link public tạm thời cần chạy lại lúc demo. |
| Tool unit tests (`tests/`) | `tests/test_compare_sources.py`, `tests/test_tools_todo.py`; `pytest` output | Test offline cho tool mới và các tool có sẵn. | Unit test không đo khả năng model chọn tool. |

Tool unit tests: `test_compare_sources.py` có 10 hàm test (một số tham số hóa thành nhiều case), gồm URL trùng, input sai và giới hạn. Lần kiểm tra toàn suite trước khi điền báo cáo: 163 passed. Không ghi nhận bug có bằng chứng chắc chắn ở tool có sẵn. Ví dụ, test URL thiếu/không hợp lệ kiểm tra code trả lỗi có kiểm soát; eval routing chỉ kiểm tra model chọn tên tool/args nên không bắt được lỗi xử lý input đó.

## B6. Reflection

- `system_prompt.md`: sửa quy tắc hỏi lại, không tự đoán tài khoản/URL, xác nhận trước action và không ép một bước. v2 cải thiện rõ nhất; v3 cho thấy quy tắc xác nhận quá rộng làm hỏi thừa.
- `tools.yaml`: khai báo `compare_sources` và mô tả input/giới hạn. Các bản base v0–v3 dùng cùng tools hash `5b22a2476d41`; group-v1 dùng `788c77a33b6b`, nên không thể gán cải thiện base cho tool declaration.
- Cần review thủ công câu trả lời sau tool: eval có thể PASS routing nhưng nguồn web không phù hợp, provider 503, hoặc UI chỉ chặn gửi chứ prompt chưa hỏi xác nhận đúng. R12 ở v3 vẫn FAIL.
- Vòng tiếp theo nên thu hẹp rule xác nhận chỉ cho `send`, yêu cầu `clarify(response_type="yes_no")` khi người dùng muốn gửi nhưng chưa xác nhận; đo lại base và group để tránh hồi quy R04/R05/M06.

## B7. Small Local Model Challenge (bonus)

Only fill if your team did the local model challenge.

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v3 | OpenRouter / `openai/gpt-4o-mini` | v3 | 80% | 85% | 80% | 83.33% | `runs/v3_B_base_openrouter_20261110T104309505202.json` |
| v3-... | Chưa chạy Ollama | — | — | — | — | — | — |
| v3-... | Chưa chạy Ollama | — | — | — | — | — | — |
| v4-local | Chưa chạy | — | — | — | — | — | — |
| v5-local | Chưa chạy | — | — | — | — | — | — |

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
