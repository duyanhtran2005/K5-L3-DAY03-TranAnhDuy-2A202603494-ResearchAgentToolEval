# Day 03 Lab v2 Report — Research Agent

## Team

- Team:
- Members:
- Provider/model: Gemini / `gemini-3.5-flash`

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research Agent là trợ lý AI hỗ trợ tìm thông tin trên web và Twitter/X, đọc nội dung từ URL, và tổng hợp dữ liệu thành bản tin có liên kết nguồn. Bộ công cụ còn hỗ trợ tra cứu chính sách nội bộ, tìm và đọc bài báo arXiv, cùng chức năng gửi bản tin lên Telegram khi được người dùng xác nhận.

**Trạng thái hiện tại:** đã kiểm tra thành công kết nối Gemini và khả năng tạo lời gọi tool `timeline`. Các chức năng dùng dịch vụ ngoài cần được cấu hình API tương ứng và kiểm thử thực tế; kết quả đánh giá sẽ được bổ sung ở Phần B.

**Link dùng thử (deploy):**

Chưa cung cấp; sẽ bổ sung URL sau khi triển khai giao diện demo.

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

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

## B5. Bonus Evidence

Only fill if your team did bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) |  |  |  |
| arXiv/company policy |  |  |  |
| UI |  |  |  |
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
