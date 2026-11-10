# Checkpoints

Bài làm nhóm. Giờ ghi cạnh mỗi checkpoint là mốc kiểm tra tại lớp, **không phải deadline**. Deadline nộp bài: 23h59 ngày lab (GMT+7), coach có thể gia hạn tối đa 48h; xem [SUBMISSION.md](SUBMISSION.md). Mọi lệnh chạy từ `starter_v0/`.

## CP1 — Setup và baseline v0 (mốc 15:00)

- **Mục tiêu:** Agent chạy được bằng provider thật và nhóm có số đo v0 để so sánh các version sau.
- **Cần làm:** Tạo repo nhóm, điền [TEAM.md](TEAM.md); cấu hình `starter_v0/.env` theo [docs/TOOL-SETUP.md](docs/TOOL-SETUP.md); chạy preflight và `pytest`; chạy base eval v0 **chưa sửa** `artifacts/system_prompt.md` và `artifacts/tools.yaml`; ghi dòng v0 vào `artifacts/version_log.csv`; gán loại lỗi cho từng case FAIL.
- **Sản phẩm:** `runs/<run v0>.json`, dòng v0 trong `version_log.csv`, bảng B2 (Failure Analysis) trong `report/team/group_report.md`.
- **Cần hiểu:** Khác nhau giữa `wrong_tool`, `wrong_arg_value`, `missing_info`, `wrong_boundary`; vì sao run có lỗi provider thì không dùng làm bằng chứng.
- **Tự kiểm tra:** `python scripts/preflight_provider.py --provider openrouter` pass; `pytest` báo contract + example test xanh, TODO test đang skipped; trong run v0 có `provider_error_cases == 0` và `measured_cases == total_cases`.

## CP2 — Tối ưu prompt và tool declaration v1–v3 (mốc 15:30 → 17:30)

- **Mục tiêu:** Cải thiện routing và arguments của agent bằng vòng lặp giả thuyết → sửa → đo.
- **Cần làm:** Mỗi version sửa **một** giả thuyết trong `artifacts/system_prompt.md` hoặc `artifacts/tools.yaml`: bỏ chỉ dẫn xấu của starter, thêm rule routing, viết lại description (khi nào dùng/không dùng), convention args, boundary xác nhận của `send`. Chạy lại base eval cho v1 (15:30), v2 (16:00), v3 (17:30); ghi từng dòng vào `version_log.csv`.
- **Sản phẩm:** Run v1, v2, v3 trong `runs/`; `version_log.csv` có hash, giả thuyết, metric trước/sau; bảng B1 trong group report.
- **Cần hiểu:** Fix nào thuộc system prompt, fix nào thuộc tool declaration; vì sao chỉ đổi một giả thuyết mỗi version.
- **Tự kiểm tra:** Mỗi version có `prompt_hash`/`tools_hash` khác version trước; `pytest tests/test_tool_contract.py` vẫn xanh; metric trước/sau đọc được từ run JSON.

## CP3 — Tool mới và unit test (mốc 15:30)

- **Mục tiêu:** Nhóm tự thêm ít nhất 1 tool và chứng minh code của tool chạy đúng.
- **Cần làm:** Tạo `tools/<tên>/tool.py` + `TOOL.md` theo `tools/README.md`; đăng ký trong `tools/__init__.py` (`TOOL_FUNCTIONS`) và `artifacts/tools.yaml`; viết ≥ 3 test trong `tests/test_tools_todo.py` (happy path, input xấu từ model, nhánh lỗi).
- **Sản phẩm:** Folder tool mới, 3 test của tool mới không còn skip, bảng B5a trong group report.
- **Cần hiểu:** Unit test đo code của tool, eval đo lựa chọn của model; vì sao tool nên trả error dict thay vì raise.
- **Tự kiểm tra:** `pytest` báo 0 failed; `pytest tests/test_tool_contract.py` xanh sau khi thêm tool.

## CP4 — Eval nhóm 10 case (mốc 16:00)

- **Mục tiêu:** Đo những lỗi nhóm quan tâm mà bộ base chưa phủ, kể cả việc route tới tool mới.
- **Cần làm:** Viết đúng 10 case trong `data/eval_group.json` (5 single turn `query`, 5 multi turn `turns`), mỗi case có `failure_type`, `expect`, `metadata.what_it_tests`; ít nhất 1 case kiểm tra route tới tool mới; chạy `--suite group`.
- **Sản phẩm:** `data/eval_group.json`, run group trong `runs/`, bảng B3 trong group report.
- **Cần hiểu:** Cách viết `expect.tool_calls` chỉ chứa args cần kiểm tra; khi nào dùng `no_tool`.
- **Tự kiểm tra:** `python run_eval.py --provider openrouter --version v3 --suite group --eval-cases data/eval_group.json` chạy không báo lỗi schema, đủ 10 case.

## CP5 — UI, live chat và báo cáo (showdown 16:30 → hoàn thiện trước deadline)

- **Mục tiêu:** Team khác dùng thử được agent; nhóm có báo cáo dựa trên bằng chứng thật.
- **Cần làm:** Làm UI (Streamlit, Vercel hoặc khác), thêm dependency vào `requirements.txt`, mở link dùng thử (Cloudflare Tunnel hoặc deploy); chạy `chat.py` ≥ 3 lượt live; điền Phần A của `report/team/group_report.md` **trước showdown 16:30**, sau đó hoàn thiện Phần B; mỗi thành viên viết `report/team/MSSV_HoTen.md`.
- **Sản phẩm:** Code UI, link dùng thử, `transcripts/*.transcript.json`, group report đủ Phần A + B, báo cáo cá nhân của từng người.
- **Cần hiểu:** Khác nhau giữa hành vi đúng (hỏi lại, xác nhận trước khi gửi) và hành vi chỉ "trả lời nghe hay"; giới hạn của chấm tự động.
- **Tự kiểm tra:** Một người ngoài nhóm mở link và chạy được câu hỏi mẫu ở A3; transcript có đủ: yêu cầu thường, thiếu thông tin rồi bổ sung, yêu cầu gửi/đăng.

Bonus (Small Local Model, thêm tool, gửi Telegram thật, test challenge) làm sau khi phần bắt buộc đã đủ; xem [RUBRIC.md](RUBRIC.md).
