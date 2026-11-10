# Rubric

| Tiêu chí | Điểm | Bằng chứng | Ghi chú |
|---|---:|---|---|
| C1 — Baseline v0 và phân tích lỗi (CP1) | 10 | Run v0 trong `starter_v0/runs/`, dòng v0 trong `starter_v0/artifacts/version_log.csv`, bảng B2 trong `report/team/group_report.md` | Mỗi case FAIL có loại lỗi và nguyên nhân. Run v0 không hợp lệ thì 0 điểm |
| C2 — Prompt và tool declaration (CP2) | 15 | `starter_v0/artifacts/system_prompt.md`, `starter_v0/artifacts/tools.yaml`, `starter_v0/tests/test_tool_contract.py` xanh | Bỏ chỉ dẫn xấu của starter; có rule routing; mỗi description nói khi nào dùng/không dùng và convention args; `send` có boundary xác nhận. Tên hoặc tham số lệch registry thì trừ điểm |
| C3 — Vòng lặp v1→v3 dựa trên bằng chứng (CP2) | 20 | Run v1, v2, v3; `starter_v0/artifacts/version_log.csv` có hash, giả thuyết, metric trước/sau; bảng B1 | Mỗi version một giả thuyết. Version chỉ đổi nhãn, thiếu run hoặc run không hợp lệ thì không tính. Version không tăng điểm vẫn được tính nếu phân tích trung thực |
| C4 — Tool mới và unit test (CP3) | 15 | `starter_v0/tools/<tên>/` (`tool.py`, `TOOL.md`), đăng ký trong `starter_v0/tools/__init__.py` + `starter_v0/artifacts/tools.yaml`; `starter_v0/tests/test_tools_todo.py`; output `pytest` | ≥ 3 test/tool (happy path, input xấu, nhánh lỗi), `pytest` 0 failed. Test gọi mạng thật, không assert gì, hoặc tool raise thay vì trả error dict thì trừ điểm |
| C5 — 10 case eval nhóm (CP4) | 10 | `starter_v0/data/eval_group.json`, run `--suite group`, bảng B3 | Đúng 5 single turn + 5 multi turn, có `expect` và `metadata.what_it_tests`, ≥ 1 case route tới tool mới. Chép case có sẵn thì không tính |
| C6 — UI và live chat (CP5) | 10 | Lệnh chạy UI và link dùng thử ở mục A1, `starter_v0/transcripts/*.transcript.json`, bảng B4 | UI chạy được theo hướng dẫn. Transcript ≥ 3 lượt gồm: yêu cầu thường, thiếu thông tin rồi bổ sung, yêu cầu gửi/đăng. Chỉ có ảnh chụp hoặc UI che lỗi tool thì không tính |
| C7 — Báo cáo nhóm (CP5) | 10 | `report/team/group_report.md` | Phần A xong trước showdown; Phần B điền đủ các mục và trỏ tới run, transcript, commit. Nhận xét không có bằng chứng thì không tính |
| C8 — Đóng góp cá nhân | 10 | `TEAM.md`, các file `report/team/MSSV_HoTen.md`, lịch sử commit | Mỗi thành viên có báo cáo đúng tên file và có commit kỹ thuật. Thiếu thành viên nào thì trừ phần của thành viên đó |
| **Tổng điểm chính** | **100** | | |

## Bonus

Bonus ghi riêng, **không cộng vào điểm chính**, tối đa 10 điểm.

| Bonus | Điểm | Bằng chứng |
|---|---:|---|
| Small Local Model Challenge (README Step 7) | 4 | ≥ 2 model local chạy base eval, ≥ 2 vòng tối ưu có log, bảng cloud vs local ở mục B7 |
| Hơn 3 tool mới (≥ 4 tool do nhóm tự viết) | 3 | Mỗi tool đủ `TOOL.md`, đăng ký, ≥ 3 test và có eval case route tới |
| Gửi Telegram thật sau khi user xác nhận | 2 | Transcript cho thấy luồng: agent hỏi lại → user xác nhận → `send(confirmed=true)` → `status: sent` trên private channel của nhóm |
| Test challenge | 1 | Toàn suite `pytest` 0 skipped, **hoặc** regression test cho bug tìm được trong tool có sẵn (ghi ở mục B5) |

Tool có sẵn trong starter (`send`, `policy`, `papers`, `paper_text`) không tự được bonus. Đổi tên tool có sẵn không được tính là tool mới.

## Quy tắc chấm

- Điểm chính tối đa: 100.
- **Run hợp lệ:** chỉ dùng run có `summary.provider_error_cases == 0` và `summary.measured_cases == summary.total_cases`.
- Bonus ghi riêng, không tự cộng vào điểm chính; tối đa 10 điểm.
- Bằng chứng phải nằm trong repo nộp bài. Nhận xét không trỏ được tới file, run hoặc commit thì không tính điểm.
