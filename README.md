# Trà Journey — Du lịch Thái Nguyên

Website tiếng Việt chạy bằng Node.js, không cần cài gói npm bên ngoài. Cần Node.js 18 trở lên.

## Chạy website trên máy hiện tại

Mở terminal tại thư mục repo `travel-web`:

```sh
cd /đường/dẫn/đến/travel-web
npm start
```

Mở <http://127.0.0.1:4173>. Giữ terminal này mở trong lúc sử dụng; nhấn `Ctrl+C` để dừng máy chủ. Tài khoản, booking và trạng thái được lưu trong `.private/`; thư mục này không được đưa lên Git. Không xóa nếu cần giữ dữ liệu hiện có.

Admin đăng nhập tại <http://127.0.0.1:4173/admin/>. Máy đã có tài khoản admin thì tiếp tục dùng tài khoản đó, không chạy lại lệnh tạo admin. Khách mở nút **Tài khoản** trên trang chủ để đăng ký hoặc đăng nhập; sau đó tạo booking và theo dõi thông báo trong mục đơn booking.

## Clone repo và chạy lần đầu

Cài Git và Node.js 18 trở lên, rồi clone repo:

```sh
git clone https://github.com/thuytrang158/UDAI_3.git
cd UDAI_3
```

Nếu GitHub yêu cầu quyền truy cập, đăng nhập tài khoản được cấp quyền với repo. Tạo `.env` từ mẫu và thêm khóa Groq của bạn để bật AI Planner/chatbot; khóa hoạt động không được lưu trong mã nguồn. Website chính không cần `npm install` vì không khai báo dependency npm. Tạo tài khoản admin lần đầu trước khi chạy website:

```sh
npm run admin:bootstrap
```

Lệnh in tên đăng nhập và mật khẩu admin ban đầu một lần. Hãy lưu mật khẩu ở nơi an toàn; lệnh chỉ dùng khi chưa có admin trong `.private/admin-users.json`. Sau đó chạy:

```sh
npm start
```

Mở <http://127.0.0.1:4173>, đăng nhập tại `/admin/`, rồi khách có thể tự tạo tài khoản bằng nút **Tài khoản**. Mỗi bản clone có kho `.private/` riêng; tài khoản admin, tài khoản khách và đơn không tự chuyển giữa các máy. Không commit hoặc gửi thư mục `.private/` cho người khác.

## Cấu hình chatbot và AI Planner (tùy chọn)

Website chính và chatbot có thể chạy riêng. Chatbot và AI Travel Planner cần khóa Groq; tạo file `.env` cục bộ từ mẫu rồi nhập khóa:

```sh
if [ ! -f .env ]; then cp .env.example .env; fi
python3 configure-groq-keys.py
```

Nhập khóa Groq vào `.env` trên máy của bạn. Có thể dùng `python3 configure-groq-keys.py` để nhập khóa mà không hiện giá trị trên màn hình, hoặc sửa thủ công các biến `GROQ_API_KEY_1` … `GROQ_API_KEY_6`. Không commit file `.env` hoặc chia sẻ khóa.

AI Planner API chạy ở cổng 8000. Mở terminal thứ hai từ thư mục gốc repo `UDAI_3` và cài môi trường Python (lần đầu):

```sh
cd Multi-Agent-AI-Travel-Planner
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Khởi động API:

```sh
uvicorn src.api:app --host 127.0.0.1 --port 8000
```

Trên Windows PowerShell, kích hoạt môi trường bằng `.venv\Scripts\Activate.ps1` thay cho lệnh `source`. Giữ cả terminal Node và terminal FastAPI mở. Website chuyển tiếp yêu cầu `/api/` tới cổng 8000; nếu FastAPI chưa chạy thì Planner và chatbot dùng RAG sẽ báo dịch vụ chưa sẵn sàng. Lần đầu khởi động FastAPI có thể tải mô hình BGE-M3 và tạo chỉ mục Qdrant; cần Internet và vài GB RAM trống. Các lần sau dùng lại chỉ mục trong `.private/qdrant`.

## Kiểm tra mã nguồn

```sh
npm run check
node check.cjs
```

`npm run check` kiểm tra cú pháp JavaScript/CJS. `node check.cjs` kiểm tra một số logic danh mục và giao diện.

## Trải nghiệm số xứ Trà

Mục **Trải nghiệm số** gộp Thái Nguyên Quest và AI Travel Planner thành một thẻ danh mục. Game được phục vụ tại `/game/`; giao diện AI Planner tại `/ai-planner/`. Các tệp game được đóng gói từ `game12/dist`; khi cập nhật game, build Vite với base `/game/` và chép bản build vào `travel-web/dist/game`.

## Chức năng

- Banner, 10 tour kết hợp phủ 13 điểm đến; lọc theo điểm đến, 1–5 ngày, giá khởi điểm và nhiều tag; sắp xếp giá.
- Chi tiết tour theo ngày/giờ, đối tượng, thể lực, mùa, di chuyển, ăn nghỉ, dịch vụ, phương án thời tiết, nguồn tham khảo; tải lịch trình Markdown.
- Yêu thích, phiếu dự toán mẫu và tải phiếu. Tour mới không có đánh giá giả.
- Thiết kế tour theo ngân sách mỗi người, số khách, thời gian, phong cách và điểm đến; dự toán chi phí, cảnh báo vượt ngân sách.
- Bản đồ Leaflet/OpenStreetMap, đánh số điểm, đường nối minh họa, liên kết chỉ đường Google Maps. Có sơ đồ dự phòng nếu Leaflet không tải.
- Lưu và tải lịch trình, viết đánh giá, tin tức/cẩm nang.
- Giao diện thích ứng màn hình nhỏ, hộp thoại bàn phím, thông báo trạng thái.

## Đặt tour

Popup chi tiết tour có quy trình chọn ngày, số khách, phương tiện, điểm đón, phòng, dịch vụ và gửi yêu cầu. Thông tin người đại diện bắt buộc; thông tin từng hành khách không bắt buộc. Yêu cầu được ghi vào kho riêng của máy chủ và xuất hiện trong bảng quản trị để nhân viên xác nhận hoặc từ chối. Dữ liệu tour lấy từ `dist/data/tour-booking-config-v2.json`. Chưa tích hợp thanh toán thật, email/SMS hoặc kết nối nhà cung cấp; trạng thái được cập nhật trong hệ thống.

API booking được xử lý cục bộ; các đơn và dữ liệu liên hệ được lưu ở `.private/booking-state.json`, bên ngoài thư mục public. Tài khoản khách hàng lưu riêng trong `.private/customer-users.json`; mật khẩu được băm bằng scrypt, cookie phiên HttpOnly và đơn được gắn với tài khoản đang đăng nhập. Trong mục tài khoản, khách xem đơn và thông báo khi admin duyệt/từ chối. Chỉ đơn đã duyệt mới cho mở màn hình QR cùng số tiền cọc và ghi nhận kết quả thành công/thất bại; QR hiện là nội dung tham chiếu nội bộ, không chuyển tiền thật. Hold hết hạn sau 10 phút. Token truy cập đơn không ghi vào localStorage hoặc URL. Giá và chỗ là dữ liệu cấu hình cần đơn vị tổ chức xác nhận; chưa kết nối ngân hàng, email hoặc SMS.

Thuật toán cá nhân hóa vẫn dùng bộ 5 điểm thử nghiệm ban đầu; bộ danh mục 10 tour chi tiết mới được quản lý riêng. Nếu chưa chọn địa điểm trong bộ thiết kế, ưu tiên phong cách và chi phí; nếu đã chọn địa điểm, giữ lựa chọn. Dự toán gồm trải nghiệm, ăn uống, lưu trú, xe nội vùng chia theo nhóm. Không phải báo giá nhà cung cấp. Tọa độ khu vực gần đúng, đường nối không phải tuyến đường bộ; kiểm tra tuyến thực tế qua Google Maps.

Bản đồ nền và phông chữ cần kết nối mạng. Ảnh bìa của cả 10 tour và bộ ảnh trong chi tiết tour dùng 8 ảnh do chủ website cung cấp từ thư mục `../images`, được sao chép nguyên bản vào `dist/assets/tours/`. Địa danh ghép theo tên tệp của chủ website, không phải kết quả xác minh địa điểm bằng hình ảnh. Ảnh nhà sàn chưa rõ địa điểm chỉ minh họa không gian lưu trú của TJ04, không đại diện cơ sở đã đặt. Không dùng ảnh có tên Juknokwon (Hàn Quốc) cho Yến Dương. Các tour có nhiều ảnh hiển thị thêm bộ ảnh bấm mở lớn; các điểm chưa có ảnh không được gán nhầm ảnh từ nơi khác. Nguồn tham khảo điểm đến được gắn vào từng tour; chỉ dùng nguồn để đối chiếu cảnh quan và vị trí, không coi là xác nhận giá/giờ/dịch vụ hiện tại.

## Dữ liệu biên tập ngày 14/10/2026

- Nguồn duy nhất: `dist/tours-data.js`; chứa 13 điểm đến, 10 tour, điều kiện chung và nguồn dẫn.
- Chạy `node export-catalogue.cjs` sau khi sửa để cập nhật `dist/data/tours.json` và `dist/data/tour-catalogue.md`.
- Chạy `npm run export:rag` để xuất `dist/data/rag-knowledge-base.json` từ dữ liệu tour, booking, ẩm thực và tin tức trên website. Tệp gồm dữ liệu gốc và `documents` dạng `{id, page_content, metadata}`; tạo embedding từ `page_content` và giữ `metadata` để trích dẫn/lọc. Có các đoạn riêng cho giá, phương tiện, lịch trình từng ngày, dịch vụ, lịch khởi hành mô phỏng và chính sách. Booking là dữ liệu demo; 30 đánh giá hư cấu chỉ lưu để kiểm kê và không đưa vào `documents`. Tin tức gồm 3 bài đầy đủ và thẻ liên kết Hồ Núi Cốc, không tải toàn văn trang ngoài. Tạo lại JSON sau khi cập nhật dữ liệu nguồn.
- `dist/tour-details.js` hiển thị chi tiết và xuất Markdown từng tour; `dist/tour-details.css` định dạng lịch trình.
- Mã TJ01–TJ10; trạng thái `draft_itinerary`; `rating: null`, `reviewCount: 0`.
- Giá là khoảng dự kiến cho đoàn 10 người lớn, ngày thường; chưa có nhà cung cấp hoặc lịch khởi hành được xác nhận. Phiếu dự toán nhân giá khởi điểm, không phải báo giá cho mọi quy mô đoàn.
- Yên Dương được chuẩn hóa thành Yến Dương (Phiêng Phàng/Pù Lầu), vẫn giữ alias để nhận diện. Chùa Hang được hiểu là Kim Sơn Tự gần trung tâm; cần đổi dữ liệu nếu chủ dự án muốn Chùa Hang ở Định Hóa.
- Địa danh theo khu vực quen thuộc, không cung cấp địa chỉ hành chính đầy đủ chưa xác minh. Tuyến Cửa Tử và Thẳm Phầy cần đơn vị chuyên môn xác nhận quyền khai thác, điều kiện nước, hướng dẫn, trang bị, bảo hiểm và phương án ứng phó trước khi nhận khách.

## Kiểm thử

`check.cjs` kiểm tra logic lọc, sắp xếp, tính ngân sách, tổng nhóm, gợi ý theo phong cách, mã hóa văn bản, độ phủ 13 điểm, 10 tour, số ngày/đêm, thứ tự thời gian, render chi tiết và tính đồng nhất JSON. Kiểm tra trực quan bằng trình duyệt chưa hoàn tất do công cụ trình duyệt lỗi khởi động sandbox Windows.


## Booking API

- `GET /api/demo/catalog` và `GET /api/demo/departures?tourCode=TJ01`
- `POST /api/demo/quote`, `/api/demo/date-requests`, `/api/demo/holds`, `/api/demo/holds/release`, `/api/demo/bookings`
- `POST /api/demo/payments/simulate`
- `GET /api/demo/bookings/:code` với header `X-Booking-Token`; các thao tác `/cancel` và `/reschedule` dùng cùng token

Chạy `npm test` để kiểm tra quote TJ01, vòng đời hold/đơn/thanh toán/hủy, bảo vệ token và chặn oversell. `npm run check` kiểm tra cú pháp các tệp JS/CJS chính.

## Quản trị đơn đặt tour

- Mở `/admin/` để đăng nhập. Tài khoản quản trị ban đầu được tạo một lần bằng `npm run admin:bootstrap`; lệnh sẽ in mật khẩu tạm thời, chỉ lưu hash mật khẩu trong `.private/admin-users.json`.
- Quản trị viên có thể xem danh sách và thông tin liên hệ của khách, tìm/lọc đơn, tải CSV, xác nhận hoặc từ chối (bắt buộc ghi lý do), quản lý tài khoản admin, đổi mật khẩu và xem nhật ký hoạt động.
- Mỗi yêu cầu được lưu bền vững trong `.private/booking-state.json`, ngoài thư mục public. Tạo `.private/` đã được thêm vào `.gitignore`. Không xóa thư mục này nếu cần giữ đơn và tài khoản.
- Phiên đăng nhập admin dùng cookie HttpOnly, SameSite Strict, hết hạn sau 8 giờ; dữ liệu thay đổi yêu cầu CSRF token. Hiện trạng thái được cập nhật trong hệ thống, chưa có dịch vụ gửi email/SMS tới khách.

## Chatbot RAG

Bong bóng **Hỏi Trà Journey** ở góc màn hình hỏi đáp về điểm đến, ẩm thực, tin tức và 10 tour trong `dist/data/rag-knowledge-base.json`. RAG và `Multi-Agent-AI-Travel-Planner` dùng chung `.env` tại thư mục gốc repo. Tạo file này từ `.env.example` và nhập khóa Groq để bật đầy đủ tính năng AI. `.env.example` không chứa khóa.

```sh
python3 configure-groq-keys.py
npm start
```

Tiện ích sẽ hỏi lần lượt tối đa sáu khóa mà không hiện nội dung khi nhập; nhấn Enter để giữ giá trị đang có. Tạo khóa trong Groq Console trước rồi dán từng khóa vào dấu nhắc tương ứng. Hoặc sửa thủ công các biến `GROQ_API_KEY_1` … `GROQ_API_KEY_6` trong `.env`. Khi Groq trả HTTP 429, RAG và Planner thử các khóa còn lại đã cấu hình. Các khóa trong cùng một tổ chức Groq thường dùng chung hạn mức tổ chức, nên xoay khóa không làm tăng quota và cũng không khắc phục được hạn mức tổ chức đã cạn; khi đó cần đợi reset hoặc xử lý hạn mức trong Groq Console. Khóa `GROQ_API_KEY` cũ vẫn được nhận để tương thích.

Mô hình mặc định là `qwen/qwen3.8-27b`; đặt `GROQ_MODEL` để đổi cho RAG và `PLANNER_GROQ_MODEL` để đổi riêng cho Planner. Python Planner đọc cùng file `.env` tại thư mục gốc repo. Để khởi động Planner trong cửa sổ terminal khác:

```sh
cd Multi-Agent-AI-Travel-Planner
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.api:app --reload --port 8000
```

Ở lần chạy đầu, FastAPI tải mô hình embedding `BAAI/bge-m3` và tạo chỉ mục Qdrant cục bộ từ knowledge base. Hãy chờ log `BGE-M3 RAG ready` trước khi hỏi chatbot; các lần sau dùng lại vector store trong `.private/qdrant`. Máy cần Internet lần đầu để tải model và nên có ít nhất vài GB RAM trống. Có thể đặt `BGE_M3_MODEL` hoặc `RAG_VECTOR_STORE_PATH` trong `.env` để tùy chỉnh.

Chỉ định một tài liệu JSON tùy chỉnh bằng cách cập nhật đường dẫn dữ liệu trong `server.cjs`.

JSON được chia thành các đoạn theo loại tài liệu và thực thể; đoạn dài được tách theo câu, giới hạn 1.800 ký tự và chồng lấn 220 ký tự. Metadata về tour, địa điểm và nguồn được giữ lại. Python mã hóa các đoạn bằng dense embedding của BGE-M3 và lưu trong Qdrant local; khi hỏi, truy xuất dense từ Qdrant được hợp nhất với BM25 bằng Reciprocal Rank Fusion (RRF, k=60). Top 5 kết quả sau hợp nhất được đưa vào context. Chỉ mục được tạo lại khi knowledge base hoặc cấu hình chunk/model đổi. Dữ liệu lịch khởi hành, giá checkout và chỗ mẫu vẫn bị loại khỏi truy vấn. Với câu hỏi về tour, chatbot bổ sung phần thông tin phù hợp của các tour được tìm thấy; tối đa sáu nguồn được gửi về giao diện.

Endpoint `POST /api/chat` giới hạn nội dung, lịch sử hội thoại và nhịp gửi; khóa Groq chỉ được đọc phía máy chủ. Node chuyển câu hỏi sang `POST /api/rag/retrieve` của FastAPI để BGE-M3 truy vấn vector store, sau đó hợp nhất với BM25/RRF và gửi context cho Qwen sinh câu trả lời. Hệ thống prompt coi tài liệu đã truy xuất là dữ liệu, không phải chỉ dẫn; chatbot không tự khẳng định thông tin thương mại chưa được xác nhận.
