# BÁO CÁO ĐỀ XUẤT TRIỂN KHAI THÍ ĐIỂM CƠ SỞ DỮ LIỆU VỀ NGƯỜI VIỆT NAM CÓ YẾU TỐ NƯỚC NGOÀI (VCFE DATABASE)

**Kính gửi:** Thủ trưởng đơn vị / Lãnh đạo Phòng

**Về việc:** Đề xuất triển khai thí điểm Phần mềm Quản trị hồ sơ nghiệp vụ an ninh (VCFE Database).

---

## I. GIỚI THIỆU CHUNG VỀ PHẦN MỀM

Hệ thống **VCFE Database (PA01)** là phần mềm đặc tả nghiệp vụ được xây dựng với mục tiêu số hóa, quản lý và khai thác hiệu quả hồ sơ đối tượng thuộc diện quản lý chuyên sâu (CSXH), có yếu tố nước ngoài hoặc các đối tượng nghiệp vụ an ninh.

Phần mềm được thiết kế tối ưu hóa cho môi trường mạng nội bộ, đảm bảo tính bảo mật cao (local/offline) kết hợp với các công cụ phân tích dữ liệu ứng dụng thuật toán thông minh, nâng cao hiệu suất làm việc của cán bộ trinh sát và cán bộ quản lý so với phương pháp thủ công hoặc trên Excel truyền thống.

---

## II. CÁC TÍNH NĂNG CHÍNH (KEY FEATURES)

Hệ thống được thiết kế dưới dạng Modular, phân loại theo nhu cầu thực tế của công tác trinh sát nghiệp vụ:

1. **Bảng điều khiển trung tâm (Dashboard)**
   - Trực quan hóa dữ liệu tổng quan dưới dạng biểu đồ (tương tác thời gian thực bằng ECharts/Plotly).
   - Thống kê tự động theo: phân bổ địa bàn (Top xã/phường), phân loại nghề nghiệp, cơ cấu giới tính, mức độ gia tăng hồ sơ.
   - Thống kê tỷ trọng các nhóm đối tượng đặc thù (Kết hôn nước ngoài, làm việc cho tổ chức NGO, Du học sinh, Vi phạm pháp luật ở nước ngoài...).

2. **Hồ sơ đối tượng toàn diện 360 độ (Profile 360)**
   Xây dựng mạng lưới thông tin liên kết xoay quanh 1 Số Định danh cá nhân (CCCD) bao gồm 8 nhóm dữ liệu lõi:
   - Thông tin cơ bản & Avatar.
   - Thông tin liên hệ (SĐT, Email, Mạng xã hội Zalo/Telegram/Facebook...).
   - Tài chính (Tài khoản ngân hàng đa nền tảng).
   - Phương tiện (Biển kiểm soát xe).
   - Các mối quan hệ nhân thân (Trực hệ & Phi trực hệ).
   - Hồ sơ nghiệp vụ đặc thù CSXH.
   - Quá trình hoạt động (Timeline).
   - Tài liệu/Chứng cứ số đính kèm (Hình ảnh, Scan PDF).

3. **Luân chuyển & Cập nhật Dữ liệu lớn (Bulk Import)**
   - Nhập liệu thủ công (Form chuẩn hóa).
   - Nhập liệu hàng loạt bằng file Excel linh hoạt qua 5 sheet riêng biệt.
   - Tự động sinh file mẫu phù hợp dựa vào loại hồ sơ muốn thao tác.

4. **Tìm kiếm & Rà soát thông minh hàng loạt (Batch Screening)**
   - Tra cứu chi tiết theo nhiều tiêu chí (Từ khóa viết tắt, địa phương, yếu tố nước ngoài...).
   - Rà soát chéo danh sách lớn: Upload 1 danh sách Excel hàng ngàn đối tượng để đối chiếu với CSDL.
   - Công cụ xuất Excel báo cáo danh sách kết quả chỉ với 1 click.

5. **Phân quyền & Giám sát An ninh (Audit & RBAC)**
   - Phân quyền theo Nhóm (Super Admin quản lý và cán bộ User nhập liệu).
   - Audit Log (Nhật ký hệ thống): Lưu vết mọi hành động Thêm/Sửa/Xóa, xem chi tiết, lịch sử xuất file của bất kỳ người dùng nào với địa chỉ IP và dán nhãn thời gian.

---

## III. LUỒNG XỬ LÝ DỮ LIỆU (DATA FLOW)

Luồng hoạt động của hệ thống được tối ưu hóa nhằm đảm bảo dữ liệu "Sạch - Sống - Bảo mật":

1. **Khâu Đầu vào (Data Ingress):**
   - **Thủ công:** Cán bộ nhập data qua giao diện Web -> Hệ thống kiểm tra Validation (tránh bỏ trống trường bắt buộc, validate định dạng cccd).
   - **Hàng loạt:** Tải lên file Excel -> Hàm `validate_excel_data` kiểm tra qua từng dòng -> Xác định các dòng lỗi (sai định dạng, thiếu CCCD). -> **Tách biệt dòng lỗi & dòng hợp lệ**.

2. **Khâu Xử lý (Data Processing & Sanitizing):**
   - Nội dung text được chuẩn hóa (loại bỏ khoảng trắng thừa, unidecode nếu cần tra cứu).
   - Hình ảnh, file đính kèm được đưa vào hàm `sanitize_filename` nhằm loại trừ triệt để mã độc hoặc các cuộc tấn công thay đổi đường dẫn (Path Traversal/Null Byte Injection), sau đó băm tạo tên file duy nhất.

3. **Khâu Lưu trữ (Storage):**
   - Dữ liệu chuẩn được đưa vào SQL Database (SQLite nội bộ chống rò rỉ).
   - Hành động lưu trữ ngay lập tức kích hoạt ghi log tự động vào bảng `audit_log`.

4. **Khâu Tra cứu/Xử lý (Retrieval & Fuzzy Match):**
   - Khi tìm kiếm/rà list: Dữ liệu tải từ DB (SQL) được đưa vào Module Python.
   - Nếu so sánh tên, sử dụng thuật toán tính vector chuỗi. Trả về mức độ tương đồng.
   - Kết xuất ra màn hình UI hoặc tải về dạng CSV có mã hóa UTF8-BOM để chống lỗi font trên Excel Windows.

---

## IV. CÁC ĐIỂM ĐỘT PHÁ CÔNG NGHỆ (CORE BREAKTHROUGHS)

Đề xuất phần mềm PA01 thay thế cách làm thủ công bởi 4 điểm đột phá mạnh mẽ:

### 1. Thuật toán Rà soát thông minh mờ (Fuzzy Matching Engine)

Khác với tính năng "Ctrl+F" trên Excel yêu cầu khớp chính xác 100%, hoặc câu lệnh SQL LIKE thông thường, hệ thống tích hợp thư viện `thefuzz/rapidfuzz`.

- Thuật toán cho phép đánh giá mức độ tương đồng của 2 chuỗi ký tự theo tỷ lệ `%`.
- **Ví dụ thực tiễn:** Tên "Nguyễn Văn An" và "Nguyễn Văn Ân" hoặc sai lệch cấu trúc "Văn An Nguyễn" vẫn được máy tính phát hiện với độ tương đồng `> 80%`. Hệ thống tự nhãn thành biểu tượng "⚠️ Nghi vấn" để cán bộ rà soát thủ công, tránh 100% tình trạng "lọt lưới" đối tượng do cố tình khai báo sai lệch một vài âm tiết.

### 2. Thuật toán Xử lý ngoại lệ Excel thông minh (Smart Bulk Import)

Khi cán bộ đưa danh sách vài nghìn dòng vào, thay vì báo lỗi toàn bộ file và từ chối nếu có 1 ô sai (như nhiều phần mềm hành chính), hệ thống có cơ chế chia tách thông minh:

- Tự động nhận diện những bản ghi hợp lệ và sẵn sàng `Import`.
- Tự động gạn lọc riêng các bản ghi lỗi, **xuất ngược lại cho người dùng 1 file Excel "Báo cáo lỗi"**, trỏ rõ chính xác dòng nào lỗi và lỗi do đâu để cán bộ sửa. Tiết kiệm tối đa thời gian làm sạch dữ liệu.

### 3. Kiến trúc Bảo mật từ cấp chứng cứ số (Zero-path-traversal)

Hệ thống được build kèm các lớp Security mặc định cho nghiệp vụ Công an:

- Session timeout nội bộ, tự đăng xuất sau 30 phút không thao tác nhằm tránh lộ lọt khi cán bộ rời vị trí.
- Cơ chế upload Avatar/Chứng cứ số chặn mã độc XSS, chặn tuyệt đối việc vượt rào thư mục cấp Server ảo.
- Ghi nhật ký mọi cú click chuột xem chi tiết đối tượng. Tránh trường hợp tra cứu chéo sai mục đích, phục vụ đắc lực công tác bảo vệ nội bộ.

### 4. Triển khai siêu di động & Nhẹ nhàng

Không yêu cầu cơ sở hạ tầng Server phức tạp hay cài đặt Database cồng kềnh (No SQL Server/MySQL required). Kiến trúc kết hợp Streamlit + SQLite được đóng gói cho phép hệ thống "Chạy trên mọi máy tính nội bộ", kể cả các máy cấu hình thấp, triển khai trong 3 phút là sẵn sàng hoạt động mà không bị phụ thuộc Internet bên ngoài.

---

## V. ĐỀ XUẤT, KIẾN NGHỊ

Từ những phân tích về hiệu quả nghiệp vụ thực tiễn nêu trên, kính đề xuất Lãnh đạo xem xét cho triển khai thí điểm phần mềm **VCFE Database** trên 01 tổ/đội chuyên trách để áp dụng nhập liệu và quản lý tệp đối tượng có yếu tố nước ngoài.

Sau 1 tháng thí điểm sẽ có báo cáo đánh giá thực tiễn về thời gian tiết kiệm được và hiệu suất trích xuất thông tin trước khi nhân rộng trong đơn vị.

Kính trình Lãnh đạo xem xét, phê duyệt./.

**Người lập báo cáo**
*(Đã ký)*
