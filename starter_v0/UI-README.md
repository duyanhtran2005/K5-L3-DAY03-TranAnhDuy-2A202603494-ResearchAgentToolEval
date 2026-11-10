# Research Desk — UI demo theo version

UI đọc run JSON và snapshot của nhóm, giữ lịch sử riêng cho v0–v3, hiển thị lời gọi tool và xuất transcript. UI không viết vào runs/, version_log.csv, artifacts/system_prompt.md, artifacts/tools.yaml hoặc tools/.

## Chạy demo

Từ thư mục gốc repository:

~~~powershell
cd starter_v0
python -m pip install -r requirements-ui.txt
python -X utf8 -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
~~~

Mở http://localhost:8501. Nếu chạy server từ môi trường giới hạn mạng, cần cho tiến trình Streamlit quyền kết nối Internet. Key lấy từ .env trên máy chủ; khởi động lại server sau khi đổi .env. Không nhập key vào chat.

## 1. So sánh Pass / Routing / Arguments / Multi-turn

Bảng đọc các file runs/**/*.json, chỉ nhận phiên bản v0, v1, v2, v3. Bộ chọn tách theo suite, provider, model và dataset để không trộn các phép đánh giá khác nhau. Trong mỗi bộ, lấy run mới nhất theo generated_at, dùng tên file làm tiêu chí phụ khi thời gian bằng nhau.

| Cột UI | summary trong run JSON |
|---|---|
| Pass | case_accuracy |
| Routing | tool_routing_accuracy |
| Arguments | argument_accuracy |
| Multi-turn | multiturn_accuracy |

Các tỷ lệ được hiển thị thành phần trăm. Giá trị thiếu, null hoặc chưa có case đo được hiển thị “—”; số 0 hợp lệ hiển thị 0.00%. Bảng cũng ghi số case đã đo/tổng số case, lỗi provider và file nguồn. “Hiện nguồn số liệu” mở summary, timestamp và hash của từng run. JSON lỗi được báo riêng, không làm mất các run đọc được.

Hiện nhánh UI chưa có run thật v0–v3. Chỉ cần nhóm bổ sung file vào runs/ rồi tải lại trang; UI không tạo số liệu mẫu trong thư mục này.

## 2. Snapshot và lịch sử riêng cho từng version

ui_versions.json ánh xạ phiên bản tới prompt và tool declaration. Ví dụ mục v2:

~~~json
{
  "prompt": "artifacts/versions/v2/system_prompt.md",
  "tools": "artifacts/versions/v2/tools.yaml",
  "prompt_hash": "<SHA-256 của đúng file prompt, nếu có>",
  "tools_hash": "<SHA-256 của đúng file tools, nếu có>"
}
~~~

Điền object đó vào versions.v2; hash là tùy chọn, bỏ hai field hash nếu chưa cung cấp (không giữ chuỗi minh họa). Đường dẫn tính từ starter_v0. UI kiểm tra hash do run JSON cung cấp ngay cả khi cấu hình không ghi hash. Nếu không khớp, phiên bản đó bị khóa chat và báo cần đúng snapshot đã đánh giá.

Khi mục cấu hình là null hoặc chưa có, UI tìm theo thứ tự:

1. artifacts/versions/vN/system_prompt.md và tools.yaml.
2. artifacts/snapshots/vN/system_prompt.md và tools.yaml.
3. ui_snapshots/vN/system_prompt.md và tools.yaml.
4. Đường dẫn system_prompt/tools trong run JSON, chỉ khi run có cả prompt_hash và tools_hash, và file hiện có khớp hai hash đó.

Đường dẫn từ checkout của máy khác được chuyển về starter_v0 hiện tại. Không dùng đường dẫn ra ngoài thư mục lab. Một đường dẫn tới prompt đang được sửa không đủ để đại diện cho version cũ: phải khớp hash hoặc có bản snapshot riêng.

v0 hiện có bản sao chính xác từng byte của prompt/tools gốc trong ui_snapshots/v0/. .gitattributes tại ui_snapshots giữ nguyên byte khi commit, để không đổi hash do xuống dòng. Đây là snapshot thật của bộ khung; v1–v3 chưa có snapshot, vì vậy UI báo thiếu thay vì gắn nhãn mới lên prompt v0. Không sửa các snapshot cũ để làm khớp điểm đánh giá; cung cấp bản đã dùng khi chạy eval.

Mỗi phiên chat giữ cố định nội dung snapshot, hai hash, provider và model lúc tạo:

- v0 → v2 → v0: lịch sử và bản nháp v0 vẫn còn.
- “Cuộc trò chuyện mới” chỉ bỏ phiên của version đang chọn; transcript đã lưu vẫn còn trên ổ đĩa.
- Đổi provider/model cho version đang chọn: bắt đầu phiên mới, không đưa lịch sử cũ sang model mới.
- Nếu đổi cấu hình khi có bản nháp gửi, UI hủy bản nháp và ghi lý do vào transcript trước khi tạo phiên mới.
- Lịch sử trong giao diện tồn tại trong phiên trình duyệt; khởi động lại server hoặc tạo phiên trình duyệt mới không tự phục hồi file transcript.

## 3. Danh sách tool và các nút thử nhanh

“Công cụ và mô tả” liệt kê các tool có sẵn, tool mới trong khai báo/registry, compare_sources và các bonus tool. Trạng thái “Sẵn sàng” yêu cầu có cả khai báo trong snapshot đang chọn và implementation trong TOOL_FUNCTIONS. UI không tự thêm hoặc sửa tool của nhóm.

compare_sources hiện được giới thiệu với đúng chức năng đối chiếu URL trùng và thống kê hostname, không chấm độ tin cậy. Khi nhóm tích hợp code + registry + khai báo vào snapshot thích hợp, nút thử sẽ tự bật sau khi khởi động lại server.

Các nút policy, papers, paper_text, lookup, compare_sources, send gửi câu hỏi mẫu đến agent. Chúng không gọi thẳng tool; phần chi tiết cho biết model có chọn đúng tool hay không.

## 4. Telegram: bản nháp, xác nhận, hủy

Model yêu cầu send (kể cả tự đặt confirmed=true) sẽ bị dừng trước khi thực thi. UI hiện đúng văn bản bản nháp; chỉ nút “Xác nhận gửi Telegram” mới gọi hàm gửi với confirmed=True. Bấm “Hủy gửi” không gọi mạng.

Khi thiếu TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID, vẫn có thể xem và hủy bản nháp; nút xác nhận bị khóa. Nếu model yêu cầu nhiều tool cùng lượt có send, UI tạm dừng toàn bộ lượt đó và chỉ xử lý bản nháp gửi đầu tiên. Các lời gọi gốc được ghi trong ui_action_gate.requested_tool_calls; lời gọi gửi thực tế được đánh dấu origin=ui_confirmation.

Token Telegram và các key đã cấu hình được che trước khi hiển thị/lưu/xuất transcript, gồm cả token trong thông báo lỗi. Bản nháp đã che thông tin bí mật cũng chính là nội dung được gửi sau khi xác nhận.

## 5. Provider / model và thông báo lỗi

Hỗ trợ Gemini, OpenRouter, Ollama, OpenAI và Anthropic bằng adapter có sẵn. Khi để trống model, UI hiển thị chính xác tên mặc định sẽ gửi tới provider. Sau khi có phản hồi, “Model phản hồi thực tế” hiển thị model/model_version do API trả về nếu có. Transcript ghi requested_model, actual_model và actual_models của từng lượt; khi API không cung cấp tên thực tế, UI giữ thông tin model yêu cầu, không tự suy đoán alias.

Thiếu key sẽ được báo ngay trong thanh bên và khóa gửi câu hỏi. Với Ollama, nút “Kiểm tra Ollama” gọi endpoint /models tại OLLAMA_BASE_URL (mặc định http://localhost:11434/v1); trước lượt chat thật cũng kiểm tra kết nối. Nếu Ollama chưa chạy, UI hướng dẫn chạy ollama serve. Lỗi model chưa tải, 429 hết quota, 503 quá tải, xác thực và chặn mạng được giải thích riêng.

## 6. Chi tiết xử lý và transcript

Mỗi câu trả lời có mục “Chi tiết xử lý” gồm tool calls, arguments, kết quả/lỗi, model thực tế và quyết định xác nhận gửi. Tải transcript JSON của version đang chọn ở thanh bên; bản sao cũng được lưu trong transcripts/*.transcript.json, kèm snapshot source và hash cho report.

## Chia sẻ bằng Cloudflare Tunnel

Giữ Streamlit chạy; ở terminal khác:

~~~powershell
cloudflared tunnel --protocol http2 --url http://127.0.0.1:8501
~~~

Nếu chưa cài:

~~~powershell
winget install --id Cloudflare.cloudflared --exact
~~~

Mở terminal mới nếu Windows chưa nhận lệnh. Dùng URL trycloudflare.com trả về cho buổi demo; link tồn tại khi máy và hai tiến trình còn chạy. Khách dùng tài nguyên API của máy chủ demo.

## Kiểm tra và gộp nhánh

~~~powershell
python -m pytest tests/test_ui_demo.py tests/test_ui_versions.py -q
~~~

Kiểm tra offline bằng fake provider và dữ liệu tạm gồm: chọn đúng snapshot, đối chiếu hash, bảng số liệu, đổi version/provider/model, nút bonus, lỗi cấu hình/Ollama, xác nhận/hủy Telegram, che token và Unicode trên Windows. Không gọi API trả phí hoặc gửi Telegram thật trong test.

Các file cần gộp: app.py, ui_session.py, ui_data.py, ui_versions.json, ui_snapshots/, requirements-ui.txt, UI-README.md, tests/test_ui_demo.py, tests/test_ui_versions.py. Giữ thay đổi sửa Unicode trước đó ở chat.py (tham số log_tool_calls); phần nâng cấp này không cần thay đổi thêm agent, provider, prompt, tool, run hay version log của nhóm.

Tham khảo: [Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest), [Cloudflare Quick Tunnels](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/).
