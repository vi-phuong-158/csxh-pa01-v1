# 🇻🇳 VCFE Database - Cơ sở dữ liệu người Việt Nam có yếu tố nước ngoài

![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.9+-green.svg)
![Framework](https://img.shields.io/badge/FastAPI-Modern-orange.svg)
![Database](https://img.shields.io/badge/SQLCipher-Encrypted-red.svg)
![UI](https://img.shields.io/badge/UI-Modern_Dark-purple.svg)

## 📝 Giới thiệu
**VCFE Database** (Vietnamese Citizens with Foreign Elements) là hệ thống quản lý cơ sở dữ liệu chuyên sâu dành cho việc theo dõi, lưu trữ và phân tích thông tin về người Việt Nam có các yếu tố liên quan đến nước ngoài. Dự án được thiết kế với tiêu chuẩn bảo mật cao, giao diện tối ưu (Modern Dark Mode) và khả năng xử lý dữ liệu phức tạp, hỗ trợ đắc lực cho công tác nghiệp vụ và quản lý nhà nước.

---

## ✨ Tính năng nổi bật
Hệ thống cung cấp các nhóm tính năng cốt lõi và nâng cao:

*   **📊 Dashboard Thông minh:** Thống kê trực quan các chỉ số quan trọng, biến động dữ liệu và biểu đồ phân bổ đối tượng theo thời gian thực.
*   **👤 Quản lý Hồ sơ 360°:** Theo dõi chi tiết thông tin định danh, quá trình hoạt động, tài chính, phương tiện và tài liệu đính kèm.
*   **🕸️ Mạng lưới Quan hệ (Network Graph):** Trực quan hóa các mối liên kết giữa các cá nhân bằng đồ thị tương tác (ECharts), hỗ trợ phân tích đa tầng (depth).
*   **🔗 Quản lý Quan hệ Chuyên sâu:** Mô hình hóa các mối quan hệ (gia đình, xã hội, nghiệp vụ) với độ tin cậy và mô tả chi tiết.
*   **🆔 Lịch sử CCCD:** Tự động theo dõi và truy vết lịch sử thay đổi số định danh cá nhân (CCCD).
*   **🔍 Tra cứu & Rà soát Nâng cao:** Tìm kiếm thông minh (Fuzzy Search), lọc dữ liệu theo nhiều tiêu chí nghiệp vụ phức tạp.
*   **📥 Nhập liệu Excel & Batch Processing:** Tự động hóa nạp dữ liệu từ file Excel mẫu, xử lý hàng nghìn hồ sơ trong vài giây.
*   **📄 Xuất báo cáo Đa dạng:** Trích xuất hồ sơ và báo cáo thống kê ra các định dạng PDF, Docx, Excel với template chuyên nghiệp.
*   **🛡️ Bảo mật Cấp độ Nghiệp vụ:** 
    *   Mã hóa toàn bộ cơ sở dữ liệu với **SQLCipher**.
    *   Phân quyền người dùng dựa trên vai trò (RBAC).
    *   Nhật ký hệ thống (Audit Log) lưu vết mọi thao tác thay đổi dữ liệu.

---

## 🛠️ Công nghệ sử dụng
Dự án áp dụng mô hình **Modern Monolith** với trải nghiệm mượt mà như SPA:

### **Backend**
*   **FastAPI:** Framework Python hiệu năng cao, xử lý Async.
*   **SQLAlchemy 2.0:** ORM tiên tiến nhất cho Python.
*   **SQLCipher:** Mã hóa AES-256 cho tệp tin SQLite.
*   **Jinja2:** Engine template render phía Server.

### **Frontend (Modern Stack)**
*   **Tailwind CSS 3.4:** Giao diện Dark Mode cao cấp, responsive.
*   **HTMX:** Xử lý tương tác động (AJAX) mà không cần viết nhiều JavaScript.
*   **Alpine.js:** Framework JS siêu nhẹ cho các micro-interaction và quản lý state phía Client.
*   **ECharts:** Thư viện đồ thị mạnh mẽ để trực quan hóa mạng lưới quan hệ.

### **Tooling & Data**
*   **Pandas & Openpyxl:** Xử lý dữ liệu Excel quy mô lớn.
*   **FPDF2 & Python-docx:** Engine xuất bản tài liệu nghiệp vụ.
*   **Uvicorn:** ASGI Server tốc độ cao.

---

## 📂 Cấu trúc thư mục
Cấu trúc dự án theo tiêu chuẩn Clean Architecture:

```text
csxh-pa01-v1/
├── backend/                # Lõi xử lý logic (Python)
│   ├── db/                 # Cấu hình Database & Session
│   ├── models/             # Định nghĩa Schema Database (SQLAlchemy)
│   ├── routes/             # API & Page Handlers (HTMX Integration)
│   ├── schemas/            # Pydantic models (Validation)
│   ├── services/           # Business logic & Phân tích mạng lưới
│   └── utils/              # Mã hóa, Export, Security helpers
├── frontend/               # Giao diện người dùng
│   ├── static/             # CSS (Tailwind), JS (HTMX/Alpine), Vendor libs
│   └── templates/          # Giao diện HTML (Jinja2 + Components)
├── scripts/                # Script khởi tạo, Backup & Migration
├── tests/                  # Bộ test đảm bảo chất lượng phần mềm
├── run_server.py           # Launcher chính (Hỗ trợ nhập Key giải mã DB)
├── requirements.txt        # Dependencies
└── tailwind.config.js      # Cấu hình Design System
```

---

## 🚀 Hướng dẫn cài đặt & Chạy dự án

### 1. Chuẩn bị môi trường
*   Cài đặt **Python 3.9** trở lên.
*   Tải bộ thư viện cần thiết.

### 2. Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### 3. Cấu hình
Sao chép file `.env.example` thành `.env` và điều chỉnh các tham số nếu cần.

### 4. Khởi chạy
Sử dụng script launcher để đảm bảo database được mở khóa đúng cách:
```bash
python run_server.py
```
Hoặc dùng file bat (Windows):
```bash
start_server.bat
```
*   **Mật khẩu DB:** Bạn sẽ được yêu cầu nhập mật khẩu để mở khóa database khi khởi chạy.
*   **Tài khoản:** Nếu là lần đầu, hãy tạo tài khoản quản trị theo hướng dẫn trên terminal.
*   **Địa chỉ:** Truy cập `http://127.0.0.1:9000` (mặc định).

---

## 🗺️ Kế hoạch phát triển (Roadmap)

1.  **🤖 Tích hợp AI Core:** Áp dụng NLP để tự động trích xuất thông tin từ tài liệu quét (OCR) và phát hiện các mẫu hành vi bất thường.
2.  **📊 Phân tích Mối liên hệ Tiềm ẩn:** Sử dụng Graph Algorithms để gợi ý các mối quan hệ chưa được khai báo dựa trên địa chỉ, số điện thoại hoặc lịch sử di chuyển.

---
*Phát triển bởi đội ngũ Kỹ thuật - VCFE Project.*
*Tác giả: Đại úy Vi Ngọc Phương - Công an tỉnh Phú Thọ.*

