# Tài Liệu Mô Tả Dự Án: Hệ Thống Cơ Sở Dữ Liệu VCFE (CSXH)

Tài liệu này cung cấp cái nhìn tổng quan về kiến trúc, công nghệ và các tính năng vận hành của hệ thống quản lý dữ liệu Chính Sách Xã Hội (VCFE Database).

---

## 1. Mục Tiêu Dự Án
Hệ thống được xây dựng nhằm tối ưu hóa quy trình quản lý hồ sơ chuyên ngành, đảm bảo tính tập trung, chính xác và bảo mật dữ liệu.
- **Tính tập trung**: Chuyển đổi từ quản lý tệp tin rời rạc sang cơ sở dữ liệu quan hệ đồng nhất.
- **Tính bảo mật**: Áp dụng các tiêu chuẩn mã hóa dữ liệu tại chỗ (at-rest) và kiểm soát truy cập nghiêm ngặt.
- **Tính linh hoạt**: Khả năng vận hành độc lập (Offline) hoặc trong mạng nội bộ (LAN), không phụ thuộc vào kết nối Internet bên ngoài.

---

## 2. Kiến Trúc Công Nghệ

Hệ thống được phát triển dựa trên các nền tảng công nghệ hiện đại, đảm bảo hiệu suất và khả năng mở rộng:

1.  **Xử lý phía máy chủ (Backend)**: Sử dụng ngôn ngữ **Python** với khung làm việc **FastAPI**. Đây là công nghệ hỗ trợ xử lý bất đồng bộ, giúp tối ưu tốc độ phản hồi và quản lý tài nguyên hệ thống hiệu quả.
2.  **Giao diện người dùng (Frontend)**: Kết hợp giữa **HTMX** và **Tailwind CSS**. 
    - HTMX giúp giảm tải cho trình duyệt bằng cách cập nhật dữ liệu từng phần mà không cần tải lại toàn bộ trang.
    - Tailwind CSS cung cấp hệ thống giao diện nhất quán, tối ưu hóa hiển thị trên nhiều loại màn hình.
3.  **Hệ quản trị cơ sở dữ liệu (Database)**: Sử dụng **SQLite** kết hợp thư viện mã hóa **SQLCipher**. 
    - Dữ liệu được bảo vệ bằng thuật toán mã hóa tiêu chuẩn quân đội (AES-256).
    - Toàn bộ tệp tin cơ sở dữ liệu sẽ bị khóa hoàn toàn, chỉ có thể truy xuất khi có mật mã xác thực chính xác.

---

## 3. Cấu Trúc Hệ Thống Và Chức Năng Thành Phần

Hệ thống được phân chia thành các lớp chức năng rõ rệt để đảm bảo tính ổn định và dễ bảo trì:

### 3.1. Thành phần Khởi động và Cấu hình
- **`start_server.bat`**: Tập lệnh thực thi nhanh trên môi trường Windows, giúp khởi động các dịch vụ cần thiết của hệ thống.
- **`run_server.py`**: Điểm nhập (Entry point) chính của ứng dụng. Thành phần này chịu trách nhiệm kiểm tra môi trường, xác thực mật mã cơ sở dữ liệu trước khi kích hoạt dịch vụ xử lý.
- **`backend/config.py`**: Quản lý tập trung các tham số cấu hình hệ thống, định mức tài nguyên và các thiết lập bảo mật.

### 3.2. Lớp Xử lý Logic (Backend)
- **`backend/models/`**: Định nghĩa cấu trúc dữ liệu và các mối quan hệ giữa các bảng thông tin trong hệ thống.
- **`backend/routes/`**: Phân tách các module tính năng nghiệp vụ:
    - `tra_cuu.py`: Xử lý các truy vấn tìm kiếm dữ liệu.
    - `nhap_lieu.py`: Quản lý quy trình tiếp nhận và lưu trữ thông tin mới.
    - `bao_cao.py`: Tổng hợp số liệu và kết xuất dữ liệu báo cáo.
    - `auth.py`: Kiểm soát định danh và quyền truy cập của người dùng.
- **`backend/services/`**: Chứa các thuật toán xử lý nghiệp vụ phức tạp và các logic tính toán chuyên sâu.

### 3.3. Lớp Giao diện (Frontend)
- **`frontend/templates/`**: Chứa các khuôn mẫu HTML, định nghĩa cấu trúc hiển thị thông tin cho người dùng.
- **`frontend/static/`**: Quản lý các tệp tin tĩnh bao gồm định dạng hiển thị (CSS), mã lệnh tương tác (JavaScript) và tài nguyên hình ảnh.

### 3.4. Lớp Lưu trữ Dữ liệu
- **`security_profile.db`**: Tệp tin cơ sở dữ liệu đã được mã hóa toàn phần, chứa toàn bộ thông tin hồ sơ của hệ thống.
- **`data/uploads/`**: Thư mục lưu trữ các tệp tin đính kèm (hình ảnh, văn bản quét) với cơ chế phân quyền truy cập chặt chẽ.
- **`data/backups/`**: Hệ thống lưu trữ các bản sao lưu định kỳ nhằm ngăn ngừa rủi ro mất mát dữ liệu do sự cố phần cứng.

---

## 4. Các Tính Năng Chức Năng

1.  **Bảng điều khiển (Dashboard)**: Cung cấp các chỉ số thống kê trực quan về tổng lượng dữ liệu và trạng thái hệ thống.
2.  **Tra cứu dữ liệu**: Hỗ trợ tìm kiếm đa tiêu chí (Số định danh, Họ tên, Đơn vị...) với thuật toán tìm kiếm tối ưu.
3.  **Quản lý hồ sơ**: Hệ thống biểu mẫu nhập liệu chuẩn hóa, hỗ trợ kiểm tra tính hợp lệ của dữ liệu ngay khi nhập.
4.  **Xử lý dữ liệu hàng loạt**: Tính năng nhập dữ liệu từ tệp tin Excel, tự động phân tích và chuẩn hóa vào cơ sở dữ liệu.
5.  **Quản trị người dùng**: Phân quyền truy cập theo vai trò (Admin, User, Viewer), đảm bảo nguyên tắc bảo mật thông tin.
6.  **Nhật ký vận hành (Audit Log)**: Ghi lại chi tiết lịch sử các thao tác thay đổi dữ liệu phục vụ công tác kiểm tra, giám sát.

---

## 5. Cơ Chế Bảo Mật

Bảo mật được thiết lập đa lớp theo tiêu chuẩn kỹ thuật:

1.  **Mã hóa dữ liệu (Encryption)**: Sử dụng SQLCipher để mã hóa toàn bộ cơ sở dữ liệu. Ngay cả khi có được tệp tin vật lý, dữ liệu vẫn không thể bị đọc nếu không có khóa giải mã.
2.  **Xác thực và Ủy quyền**: Hệ thống sử dụng cơ chế phiên làm việc (Session) bảo mật. Người dùng phải được cấp tài khoản định danh và phân quyền cụ thể trước khi truy cập.
3.  **Phòng thủ tấn công (Web Security)**:
    - **CSRF Protection**: Ngăn chặn các cuộc tấn công giả mạo yêu cầu từ trang web khác.
    - **Rate Limiting**: Giới hạn tần suất yêu cầu để ngăn chặn các cuộc tấn công dò tìm mật mã (Brute-force).
4.  **Bảo mật tham số**: Các thông tin nhạy cảm (Secret Key, DB Password) không được lưu trữ cứng trong mã nguồn hoặc tệp tin cấu hình, mà được nhập trực tiếp khi khởi động dịch vụ.

---

## 6. Phụ Lục: Giải Thích Thuật Ngữ Kỹ Thuật

1.  **Backend**: Phần xử lý logic phía máy chủ, chịu trách nhiệm tương tác với cơ sở dữ liệu và thực hiện các tính toán.
2.  **Frontend**: Phần giao diện hiển thị trên trình duyệt, cho phép người dùng tương tác với hệ thống.
3.  **Cơ sở dữ liệu (Database)**: Tập hợp các dữ liệu được tổ chức có cấu trúc để dễ dàng quản lý và truy xuất.
4.  **SQLCipher**: Phần mở rộng của SQLite hỗ trợ mã hóa 256-bit AES cho tệp tin dữ liệu.
5.  **Offline**: Trạng thái hoạt động trong môi trường mạng nội bộ, không yêu cầu kết nối với mạng Internet công cộng.
6.  **CSRF (Cross-Site Request Forgery)**: Một loại tấn công giả mạo yêu cầu từ người dùng đã được xác thực đến hệ thống.
7.  **Rate Limiting**: Cơ chế kiểm soát lưu lượng truy cập nhằm đảm bảo tính ổn định và ngăn chặn các hành vi truy cập tự động bất thường.
8.  **Audit Log**: Tập nhật ký ghi lại các sự kiện quan trọng trong hệ thống phục vụ mục đích truy vết.
9.  **AES-256**: Tiêu chuẩn mã hóa tiên tiến nhất hiện nay, được sử dụng rộng rãi để bảo vệ dữ liệu nhạy cảm.

---
*Tài liệu kỹ thuật nội bộ. Mọi thay đổi về kiến trúc cần được phê duyệt bởi bộ phận phát triển.*
