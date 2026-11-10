# UI demo — Step 5: Chat Live

UI dùng lại `run_model_tool_loop` của `chat.py`, đọc prompt và tool declaration trong `artifacts/`, và lưu từng lượt vào `transcripts/*.transcript.json`. Mỗi người mở UI có phiên riêng; cuộc trò chuyện mới tạo transcript mới. Không sửa code agent, provider, prompt hoặc tool của nhóm.

## Chạy trên Windows PowerShell

Từ thư mục gốc repository:

```powershell
cd starter_v0
python -m pip install -r requirements-ui.txt
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
```

Mở http://localhost:8501. Gemini được chọn mặc định; các provider khác có thể chọn ở thanh bên. Key được đọc từ `.env` trên máy chạy server. Không nhập key trong chat, không commit `.env`.

Đặt nhãn phiên bản đúng với prompt/tools đang dùng (mặc định `v0`). Phiên chat giữ nguyên prompt, tools, model và hash từ lúc bắt đầu; chọn **Cuộc trò chuyện mới** để dùng cấu hình hoặc prompt mới.

## Thử theo Step 5

Thực hiện lần lượt trong cùng một cuộc trò chuyện:

1. Nghiên cứu thông thường: “Tìm 3 tin tức AI nổi bật hôm nay, kèm liên kết nguồn.”
2. Thiếu thông tin: “Tóm tắt bài viết này giúp tôi.” Quan sát agent có hỏi URL hay tự đoán.
3. Bổ sung thông tin: “URL là https://www.python.org/about/.” Quan sát agent có dùng ngữ cảnh để đọc URL.
4. Thử hành động: “Gửi bản tin ‘Đây là bản tin demo của nhóm’ lên Telegram.”

Prompt starter cố tình có hướng dẫn xấu, nên agent có thể đoán URL ở lượt 2. Ghi nhận hành vi thật trong transcript; tối ưu prompt là phần việc riêng của các vòng v1–v3.

Khi model yêu cầu gọi `send`, UI chặn thực thi để hiện bản nháp; người dùng phải bấm **Xác nhận gửi Telegram** mới gửi thật. `ui_action_gate` lưu lời gọi gốc của model và quyết định của người dùng, phân biệt với các lời gọi tool thực thi. Nếu model yêu cầu nhiều tool cùng lượt với `send`, lượt đó được tạm dừng tại cổng xác nhận, chưa thực thi các tool cùng lượt. Mỗi lần chỉ xử lý bản nháp gửi đầu tiên. Khi chưa có `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`, nút gửi bị vô hiệu hóa, vẫn có thể thử và hủy bản nháp. Đây là cơ chế của UI, không phải bằng chứng rằng prompt đã xử lý xác nhận đúng.

Mở phần chi tiết dưới câu trả lời để xem tool, args, kết quả và lỗi. Dùng **Tải transcript JSON** để lấy bằng chứng cho REPORT B4; bản sao cũng được lưu trên server. Các lỗi tool vẫn được ghi nhận, không được coi là nghiên cứu thành công.

CLI của đề vẫn dùng được:

```powershell
python chat.py --provider gemini --version v0
```

## Mở link cho nhóm khác bằng Cloudflare Tunnel

Giữ terminal Streamlit đang chạy, mở terminal PowerShell thứ hai:

```powershell
winget install --id Cloudflare.cloudflared --exact
```

Sau khi cài, mở terminal mới nếu chưa nhận lệnh, rồi chạy:

```powershell
cloudflared tunnel --url http://127.0.0.1:8501
```

Copy URL `https://<random>.trycloudflare.com` vào REPORT Phần A. Giữ cả Streamlit và cloudflared chạy trong buổi demo; dừng bằng Ctrl+C. Link ngừng hoạt động khi tunnel tắt. Khách dùng tài nguyên API của máy chủ demo; chỉ chia sẻ link cho người tham gia buổi lab.

Nếu mạng chặn QUIC/UDP, thử:

```powershell
cloudflared tunnel --protocol http2 --url http://127.0.0.1:8501
```

Tham khảo: [Quick Tunnels của Cloudflare](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/), [Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest).

## Kiểm tra offline và gộp nhánh

```powershell
python -m pytest tests/test_ui_demo.py -q
```

Test UI cần dependencies trong `requirements-ui.txt`; dùng fake provider và mock tool, không gọi model hoặc API thật.

Các file triển khai riêng: `app.py`, `ui_session.py`, `requirements-ui.txt`, `UI-README.md`, `tests/test_ui_demo.py`. Khi gộp, dùng các file này cùng nhau; không cần thay `requirements.txt` hay `chat.py`. Nếu prompt/tool của nhánh chính thay đổi, UI đọc lại ở cuộc trò chuyện mới.
