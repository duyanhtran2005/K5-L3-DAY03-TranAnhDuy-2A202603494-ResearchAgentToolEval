# Submission

## Loại bài

**Nhóm.** Nhóm push bài lên GitHub; mỗi thành viên tự nộp cùng link repo nhóm trên LMS bằng tài khoản cá nhân.

## Tên repo và biến tên

- `Kn`: số khóa. Khóa này dùng `K5`.
- Level/lớp: `L3A` hoặc `L3B`, theo lớp bạn học.

### Repo bài nộp nhóm

```text
K5-L3A-DAY03-TenNhom-ResearchAgentToolEval
K5-L3B-DAY03-TenNhom-ResearchAgentToolEval
```

`TenNhom` viết không dấu, không khoảng trắng.

### Tạo repo nhóm

Khi repo đề bài cho phép Fork, nhóm trưởng Fork rồi đổi tên theo mẫu trên. Nếu không Fork được, clone repo đề bài, đổi `origin` sang repo nhóm rỗng và push `main`:

```powershell
git clone https://github.com/VinUni-AI20k/Day03-Prompt-Engineering-Tool-Calling-Labs-student.git <TEN_REPO_NHOM>
cd <TEN_REPO_NHOM>
git remote rename origin upstream
git remote add origin <URL_REPO_NHOM>
git push -u origin main
```

## Cấu trúc và deliverable phải nộp (đặt tên và cấu trúc)

### Báo cáo và thông tin nhóm

- `TEAM.md` (root): điền đầy đủ thông tin nhóm, thành viên và phân công.
- Báo cáo nhóm: `report/team/group_report.md` (Phần A + Phần B).
- Mỗi thành viên nộp một báo cáo cá nhân: `report/team/MSSV_HoTen.md` (ví dụ: `report/team/20241234_NguyenVanAn.md`), copy từ file mẫu `report/team/MSSV_HoTen.md`.
- Poster Phần A (tùy chọn): `report/team/poster.html` hoặc `report/team/poster.svg`.

### Code và evidence trong `starter_v0/`

| Phần | File |
|---|---|
| Prompt và tool declaration | `artifacts/system_prompt.md`, `artifacts/tools.yaml` (khớp `tools/__init__.py`) |
| Thử nghiệm v0–v3 | `artifacts/version_log.csv` có ít nhất `v0`–`v3`, `runs/*.json` tương ứng |
| Tool mới | `tools/<tên>/tool.py` + `TOOL.md`, đăng ký trong `tools/__init__.py` và `tools.yaml` |
| Unit test | `tests/` (≥ 3 test cho mỗi tool mới, `pytest` 0 failed) |
| Eval nhóm | `data/eval_group.json` đúng **10 case: 5 single turn + 5 multi turn**, kèm run `--suite group` |
| UI và transcript | Code UI, dependency UI trong `requirements.txt`, lệnh chạy UI ghi ở mục A1 của group report; `transcripts/*.transcript.json` |
| Phân tích (tùy chọn) | `analysis/*.csv` nếu parse run log |
| Bonus (nếu làm) | Run JSON của model local, prompt/tools riêng cho local; transcript gửi Telegram |

Run dùng làm bằng chứng phải có `provider_error_cases == 0` và `measured_cases == total_cases` trong `summary`. Cách chấm xem [RUBRIC.md](RUBRIC.md).

Không commit `.env`, API key, token Telegram, `.venv`, cache hay `arxiv_papers/`.

## Deadline (GMT+7)

- Deadline mặc định: **23h59 ngày lab (GMT+7)**. Coach có thể gia hạn tối đa 48h; nếu gia hạn thì theo thông báo của coach.
- Các mốc trong [CHECKPOINTS.md](CHECKPOINTS.md) chỉ là checkpoint tại lớp, không phải deadline.
- Sửa sau deadline phải tạo commit hoặc branch mới; xem [RULES.md](RULES.md).

## Checklist

- [ ] Đổi tên repo theo đúng quy ước `K5-L3A-…` hoặc `K5-L3B-…`.
- [ ] Điền thông tin vào `TEAM.md` ở root, ghi commit chốt.
- [ ] Mỗi thành viên có file báo cáo đã đổi tên đúng định dạng `report/team/MSSV_HoTen.md`.
- [ ] `report/team/group_report.md` điền đủ Phần A và Phần B.
- [ ] Mỗi thành viên có commit kỹ thuật trong lịch sử branch nộp bài.
- [ ] `cd starter_v0 && pytest` báo 0 failed.
- [ ] Có đủ run v0–v3, run group, transcript và UI chạy được.
- [ ] Không sửa nội dung case trong `data/eval_base.json`; không commit secret, password, file `.env`.
- [ ] Đã push lên GitHub; repo mở được cho người chấm.
- [ ] Mọi thành viên đã nộp cùng link repo trên LMS trước deadline.
