# MÔ TẢ CHI TIẾT DỰ ÁN (SECURITY PROFILE 360)

## 1. Giới thiệu chung
**Tên dự án:** Hệ thống Quản trị An ninh PA01 (Security Profile 360)
**Mục tiêu:** Số hóa, quản lý và khai thác hiệu quả hồ sơ đối tượng thuộc diện quản lý chuyên sâu (CSXH), đối tượng có yếu tố nước ngoài hoặc các diện đối tượng nghiệp vụ an ninh khác.

### Công nghệ sử dụng
- **Giao diện người dùng (Frontend):** Streamlit (Python).
- **Tiến trình xử lý (Backend):** Python (`services.py`, `auth.py`, `database.py`, `utils`).
- **Cơ sở dữ liệu (Database):** SQLite (`security_profile.db`).
- **Thư viện cốt lõi:** `pandas` (xử lý dữ liệu lớn), `thefuzz`/`rapidfuzz` (thuật toán rà soát/so khớp mờ), `ECharts`/`Plotly` (vẽ biểu đồ trực quan).

### Kiến trúc Dữ liệu "Profile 360 độ"
Điểm lõi của hệ thống là xoay quanh **Số Định danh cá nhân (CCCD)**, tạo ra một mạng lưới thông tin vệ tinh bao gồm 8 nhóm dữ liệu:
1. **Thông tin gốc (Đối tượng):** Tên, năm sinh, quê quán, nghề nghiệp, ảnh chân dung.
2. **Thông tin Liên hệ:** Số điện thoại, Email, Mạng xã hội.
3. **Tài chính:** Tài khoản ngân hàng, ví điện tử.
4. **Phương tiện:** Các phương tiện đăng ký.
5. **Nhân thân:** Quan hệ gia đình, thân nhân.
6. **Hồ sơ Đặc thù:** Các yếu tố nghiệp vụ CSXH.
7. **Quá trình hoạt động:** Dòng thời gian (Timeline) theo dõi di biến động.
8. **Tài liệu đính kèm:** Hồ sơ chứng cứ, tài liệu scan.

### Các tính năng Đột phá & An toàn
- **Dashboard trực quan:** Thống kê theo xã/phường, nhóm đối tượng thông qua biểu đồ tự động.
- **Nhập liệu & Xử lý Excel thông minh (Smart Bulk Import):** Quản lý đầu vào qua Upload Excel hàng nghìn dòng. Lọc lỗi thông minh.
- **Rà soát danh sách chéo bằng So khớp mờ (Fuzzy Matching):** So khớp tương đối, không yêu cầu khớp 100%.
- **Bảo mật Nội bộ & Phân quyền (Audit Trails & RBAC):** Phân quyền Super Admin / User, nhật ký lưu vết mọi thao tác (Audit Log), chống Path Traversal.

---

## 2. SƠ ĐỒ LUỒNG XỬ LÝ (PROCESSING FLOW DIAGRAM)
Hệ thống xử lý phân tầng rõ ràng từ Frontend (Giao diện người dùng) -> Backend (Xử lý Python) -> Database (SQLite).

```mermaid
block-beta
  columns 3

  %% Hàng 1: Người dùng và Giao diện
  User(("Cán bộ\nSử dụng"))
  Admin(("Super Admin"))
  Login["Đăng nhập\nAuthentication"]
  User --> Login
  Admin --> Login
  
  %% Row 2: Khối chức năng Frontend
  space
  block:Frontend:3
    columns 5
    Dash["Dashboard\nTổng quan"]
    InputM["Nhập liệu\nThủ công"]
    InputE["Nhập Excel\nHàng loạt"]
    Search["Tra cứu &\nRà soát chéo"]
    SysAdmin["Quản lý Hệ thống\n& Ghi Log"]
    
    Dash --> InputM
    Dash --> InputE
    Dash --> Search
    Dash --> SysAdmin
  end

  %% Liên kết từ Login xuống Frontend
  Login --> Frontend

  %% Row 3: Logic Xử lý Backend
  space
  block:Backend:3
    columns 5
    Auth["Xác thực\nThẩm quyền"]
    Valid["Chuẩn hóa &\nKiểm duyệt đầu vào"]
    Parser["Tách bản ghi\nHợp lệ / Lỗi"]
    FileProcess["Xử lý File &\nChặn mã độc"]
    Fuzzy["Thuật toán mờ\n(Fuzzy Match)"]

    Auth --> Valid
    Parser --> Valid
  end

  %% Liên kết Frontend xuống Backend
  InputM --> Valid
  InputE --> Parser
  Search --> Fuzzy
  SysAdmin --> Auth

  %% Row 4: Cơ sở dữ liệu SQLite
  space
  block:Database:3
    columns 5
    DBUser[("Tài khoản User")]
    DBMain[("Dữ liệu Lõi\n(Đối tượng)")]
    DBSatellite[("Dữ liệu Vệ tinh\n(8 bảng)")]
    DBAudit[("Lịch sử thao tác\n(Audit Log)")]
    DBSource[("Nguồn OSINT\n(Import log)")]
  end

  %% Tương tác Backend - Database
  Auth --> DBUser
  Valid --> DBMain
  Valid --> DBSatellite
  FileProcess --> Storage[("Kho Upload\nFiles/Avatar")]
  Fuzzy --> DBMain

  %% Luồng kích hoạt Audit (Nhật ký)
  DBMain --> DBAudit
  DBSatellite --> DBAudit
  SysAdmin --> DBAudit

  %% Xử lý kết quả phản hồi lên Frontend
  Parser --> FileError["File Excel Báo lỗi"]
  Fuzzy --> Res["Hiện Kết quả &\nCảnh báo độ trùng khớp"]

  %% Định dạng màu sắc sơ đồ (Styling tùy chọn)
  style Frontend fill:#eef,stroke:#333,stroke-width:2px;
  style Backend fill:#eaf8e6,stroke:#333,stroke-width:2px;
  style Database fill:#fdf1e6,stroke:#333,stroke-width:2px;
```
