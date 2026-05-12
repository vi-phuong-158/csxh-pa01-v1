# 🇻🇳 VCFE Database - Hệ thống quản lý người Việt Nam có yếu tố nước ngoài (v2.0)

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.10+-green.svg)
![Framework](https://img.shields.io/badge/FastAPI-High_Performance-orange.svg)
![Security](https://img.shields.io/badge/SQLCipher-AES_256-red.svg)
![Auth](https://img.shields.io/badge/Windows_Credential-Keyring-blueviolet.svg)

## 📝 Giới thiệu
**VCFED v2.0** (Vietnamese Citizens with Foreign Elements Database) là phiên bản nâng cấp toàn diện, được thiết kế chuyên biệt để theo dõi, quản lý và phân tích mạng lưới đối tượng có yếu tố nước ngoài. 

Với triết lý **"Zero-Configuration Security"**, phiên bản 2.0 loại bỏ sự phụ thuộc vào các file `.env` nhạy cảm, thay thế bằng cơ chế bảo mật tích hợp sâu vào Hệ điều hành Windows, mang lại trải nghiệm "mở là chạy" nhưng vẫn đảm bảo tiêu chuẩn an ninh nghiêm ngặt nhất của ngành.

---

## ✨ Tính năng nổi bật (v2.0)
Hệ thống kế thừa các tính năng cốt lõi và bổ sung những nâng cấp đột phá:

*   **🛡️ Bảo mật "Enter-Once"**: Tích hợp **Windows Credential Manager**. Người dùng chỉ cần nhập mật khẩu CSDL một lần duy nhất; hệ thống sẽ tự động lưu trữ mã hóa và tự động mở khóa cho các lần khởi động sau.
*   **📊 Dashboard Phân tích Nâng cao**: Ngoài thống kê đối tượng, Dashboard v2.0 tích hợp biểu đồ theo dõi hoạt động hệ thống (lượt truy cập, thao tác đọc/ghi) theo thời gian thực.
*   **🕸️ Phân tích Mạng lưới 4D**: Trực quan hóa mối liên hệ đa tầng bằng đồ thị tương tác, hỗ trợ lọc sâu theo tính chất quan hệ và mức độ tin cậy.
*   **📱 Trải nghiệm Người dùng (UX) Hiện đại**:
    *   Giao diện **Glassmorphism Dark Mode** cao cấp.
    *   Cơ chế **"Load More" Pagination**: Tối ưu hóa hiệu năng và trải nghiệm vuốt chạm trên thiết bị di động.
    *   **Smart Greetings**: Giao diện cá nhân hóa theo thời gian trong ngày.
*   **⚙️ Khởi động Tự động (Smart Launcher)**:
    *   Tự động phát hiện và giải phóng cổng (Port) nếu bị treo.
    *   Tự động mở trình duyệt ngay khi server sẵn sàng.
    *   Hộp thoại GUI chuyên nghiệp với logo nhận diện thương hiệu.
*   **🔒 An toàn Dữ liệu Tuyệt đối**:
    *   Mã hóa **SQLCipher AES-256**.
    *   **Deterministic Secret Key**: Khóa ký JWT được sinh tự động từ mật khẩu DB bằng thuật toán PBKDF2, loại bỏ việc lưu khóa bí mật trong file văn bản.

---

## 💻 Tech Stack Hiện đại
Dự án áp dụng mô hình **Modern Monolith** tối ưu hóa cho môi trường Offline:

*   **Backend**: FastAPI, SQLAlchemy 2.0 (Async Core), SQLCipher.
*   **Security**: Keyring (Windows Credential Manager), PBKDF2-SHA256, Bcrypt.
*   **Frontend**: Tailwind CSS 3.4, HTMX (xử lý động không reload), Alpine.js (state management), ECharts.
*   **Data**: Pandas, OpenPyXL, FPDF2, Python-docx.

---

## 📂 Cấu trúc thư mục
```text
csxh-pa01-v1/
├── backend/                # Lõi xử lý logic (Python)
│   ├── db/                 # Cấu hình Database & Session (SQLCipher)
│   ├── models/             # Định nghĩa Schema Database (SQLAlchemy 2.0)
│   ├── routes/             # Handlers (Tích hợp HTMX & Jinja2)
│   ├── services/           # Logic nghiệp vụ & Phân tích đồ thị
│   └── utils/              # Security (PBKDF2), Export helpers
├── frontend/               # Giao diện người dùng
│   ├── static/             # Assets (Tailwind, HTMX, Alpine, Lucide)
│   └── templates/          # Jinja2 Templates & Components
├── assets/                 # Tài nguyên thương hiệu (Logo, Icons)
├── run_server.py           # Launcher thông minh (GUI, Keyring, Port Fix)
└── requirements.txt        # Danh sách thư viện (Đã bổ sung keyring)
```

---

## 🚀 Hướng dẫn khởi chạy

### 1. Cài đặt môi trường
*   Yêu cầu **Python 3.10** hoặc cao hơn.
*   Cài đặt thư viện: `pip install -r requirements.txt`

### 2. Khởi chạy hệ thống
Chạy lệnh sau hoặc double-click vào file `.bat` tương ứng:
```bash
python run_server.py
```

### 3. Quy trình bảo mật (Chỉ lần đầu)
1.  **Mật khẩu CSDL**: Một hộp thoại GUI sẽ hiện lên. Hãy nhập mật khẩu giải mã tệp tin `.db`. Mật khẩu này sẽ được lưu an toàn vào Windows Credential Manager.
2.  **Tạo Admin**: Nếu là lần đầu chạy trên DB mới, hệ thống sẽ yêu cầu bạn tạo mật khẩu quản trị cấp cao nhất.
3.  **Sử dụng**: Trình duyệt sẽ tự động mở trang chủ `http://127.0.0.1:9000`.

*Lưu ý: Từ lần khởi động thứ 2, bạn không cần nhập lại bất kỳ mật khẩu nào trừ khi bạn đổi máy tính hoặc thay đổi mật khẩu CSDL.*

---

## 🗺️ Lộ trình (Roadmap)
1.  **🔍 Fuzzy Search Toàn diện**: Tích hợp `RapidFuzz` sâu hơn vào mọi trường thông tin để tìm kiếm hồ sơ dù sai lệch dấu hoặc định dạng.
2.  **📈 Export Template Builder**: Cho phép người dùng tự định nghĩa mẫu báo cáo Word/PDF bằng cách kéo thả các trường thông tin.

---
*Phát triển bởi đội ngũ Kỹ thuật PA01 - Công an tỉnh Phú Thọ.*
*Chủ nhiệm dự án: Đại úy Vi Ngọc Phương.*
