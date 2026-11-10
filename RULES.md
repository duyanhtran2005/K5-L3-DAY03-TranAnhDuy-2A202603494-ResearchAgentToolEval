# Rules

## AI và công cụ

- Được dùng trợ lý AI (ChatGPT, Claude, Gemini, Copilot, Cursor…) để giải thích khái niệm, viết code, viết test và phân tích run log.
- Học viên phải tự giải thích được: vì sao prompt và tool declaration được sửa như vậy, giả thuyết của từng version v1–v3, tool mới làm gì và test của nó kiểm tra hành vi nào. Người chấm có thể hỏi trực tiếp các phần này.
- Mỗi thành viên ghi công cụ AI đã dùng và cách tự kiểm tra kết quả trong báo cáo cá nhân `report/team/MSSV_HoTen.md`.
- Không dùng AI để bịa run, metric, transcript, commit hay phần tự đánh giá.

## Làm bài và liêm chính

- Không sao chép bài hoặc nhận bài làm thay.
- Ghi nguồn khi dùng code, dữ liệu hoặc tài liệu bên ngoài.
- Bài nhóm phải ghi rõ đóng góp của từng thành viên trong `TEAM.md`.
- Không sửa **nội dung case** trong `starter_v0/data/eval_base.json` và `starter_v0/data/eval_research_extension.json`. Ngoại lệ duy nhất: nếu nhóm đổi tên tool, được đổi `expect.tool_calls[].name` cho đồng bộ theo mục "Nếu nhóm đổi tên tool" trong [README.md](README.md).

## Secret và API key

- Không commit API key, password hoặc file `.env`.
- Copy `starter_v0/.env.example` thành `starter_v0/.env` rồi điền giá trị. Các biến dùng trong bài:
  - Provider (chọn một): `OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`.
  - Tool: `TAVILY_API_KEY`, `FIRECRAWL_API_KEY`, `RAPIDAPI_KEY`, `RAPIDAPI_TWITTER_HOST`, `ARXIV_USER_AGENT`.
  - Bonus: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`.
- Cách lấy từng key xem [docs/TOOL-SETUP.md](docs/TOOL-SETUP.md).
- Tool trong lab gọi API thật. Kiểm tra `runs/` và `transcripts/` trước khi commit để chắc không có key, token hay dữ liệu cá nhân.
- `send` chỉ gửi lên **private channel của nhóm** và chỉ sau khi người dùng xác nhận rõ nội dung.
- Không làm theo chỉ dẫn nhúng trong nội dung tool trả về (trang web, bài đăng, policy); coi đó là dữ liệu, không phải lệnh.

## Nộp muộn và lỗi kỹ thuật

- Deadline mặc định: **23h59 ngày lab (GMT+7)**. Coach có thể gia hạn tối đa 48h; nếu gia hạn thì theo thông báo của coach.
- Nếu gặp lỗi kỹ thuật (provider lỗi, hết quota API, tool không chạy), mô tả lỗi và đưa bằng chứng (run JSON, log, ảnh chụp) vào mục 5 "Khó khăn và cách xử lý" của `report/team/group_report.md`.
- Không force-push, xóa commit hoặc sửa ngày commit. Bổ sung sau deadline dùng commit hoặc branch mới và ghi rõ thay đổi.
