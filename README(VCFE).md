# 🇻🇳 VCFE Database - Cơ sở dữ liệu người Việt Nam có yếu tố nước ngoài

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.9+-green.svg)
![Framework](https://img.shields.io/badge/FastAPI-Modern-orange.svg)
![Database](https://img.shields.io/badge/SQLCipher-Encrypted-red.svg)

## 📝 Giới thiệu
**VCFE Database** (Vietnamese Citizens with Foreign Elements) là hệ thống quản lý cơ sở dữ liệu chuyên sâu dành cho việc theo dõi, lưu trữ và phân tích thông tin về người Việt Nam có các yếu tố liên quan đến nước ngoài. Dự án được thiết kế với tiêu chuẩn bảo mật cao, giao diện hiện đại và khả năng xử lý dữ liệu quy mô lớn, hỗ trợ đắc lực cho công tác nghiệp vụ và quản lý nhà nước.

---

## ✨ Tính năng nổi bật
Dựa trên phân tích mã nguồn, hệ thống cung cấp các nhóm tính năng cốt lõi sau:

*   **📊 Dashboard Tổng quát:** Cung cấp biểu đồ thống kê trực quan, theo dõi biến động dữ liệu và tình trạng hồ sơ theo thời gian thực.
*   **👤 Quản lý Hồ sơ Chi tiết (DoiTuong):** Quản lý thông tin định danh (CCCD), quá trình hoạt động, mối quan hệ thân nhân, tài chính và phương tiện của từng cá nhân.
*   **🔍 Tra cứu & Rà soát Thông minh:** Tìm kiếm nâng cao theo nhiều tiêu chí, hỗ trợ quy trình rà soát và xác minh thông tin đối tượng.
*   **📥 Nhập liệu Excel (Batch Import):** Tự động hóa việc nạp dữ liệu từ các tệp Excel mẫu, giúp tiết kiệm thời gian và giảm thiểu sai sót thủ công.
*   **📄 Xuất báo cáo Đa dạng:** Hỗ trợ trích xuất dữ liệu ra các định dạng chuyên dụng (PDF, Docx, Excel) phục vụ công tác báo cáo.
*   **🛡️ Bảo mật & Nhật ký (Audit Log):** Hệ thống mã hóa cơ sở dữ liệu (SQLCipher), quản lý phân quyền người dùng (RBAC) và lưu vết mọi tác động lên hệ thống.
*   **📅 Lịch sự kiện:** Theo dõi và quản lý các mốc thời gian quan trọng liên quan đến đối tượng hoặc hồ sơ nghiệp vụ.

---

## 🛠️ Công nghệ sử dụng
Dự án áp dụng mô hình **SSR (Server-Side Rendering)** kết hợp với các công nghệ hiện đại:

### **Backend**
*   **FastAPI:** Framework Python hiệu năng cao, xử lý bất đồng bộ (Async).
*   **SQLAlchemy 2.0:** ORM mạnh mẽ để tương tác với cơ sở dữ liệu.
*   **SQLCipher:** Mã hóa toàn bộ tệp tin database SQLite ở cấp độ lưu trữ.
*   **Jinja2:** Engine template để render giao diện phía Server.

### **Frontend**
*   **Tailwind CSS 3.4:** Framework CSS tiện ích cho giao diện hiện đại và responsive.
*   **Vanilla JS:** Xử lý các tương tác micro-interaction trên trình duyệt.

### **Tooling & Data**
*   **Pandas & Openpyxl:** Xử lý và phân tích dữ liệu Excel.
*   **FPDF2 & Python-docx:** Xuất bản tài liệu chuyên nghiệp.
*   **Uvicorn:** ASGI Server vận hành ứng dụng.

---

## 📂 Cấu trúc thư mục
Cấu trúc dự án được tổ chức theo tiêu chuẩn sạch (Clean Architecture):

```text
csxh-pa01-v1/
├── backend/                # Lõi xử lý logic (Python)
│   ├── db/                 # Kết nối và cấu hình Database
│   ├── models/             # Định nghĩa Schema Database (SQLAlchemy)
│   ├── routes/             # Định nghĩa API và Controllers (Page Handlers)
│   ├── schemas/            # Pydantic models (Validation dữ liệu)
│   ├── services/           # Business logic xử lý nghiệp vụ
│   └── utils/              # Các hàm bổ trợ (Mã hóa, Export, ...)
├── frontend/               # Giao diện người dùng
│   ├── static/             # CSS (Tailwind), JS, Hình ảnh
│   └── templates/          # Giao diện HTML (Jinja2)
├── scripts/                # Các script khởi tạo và bảo trì hệ thống
├── tests/                  # Mã nguồn kiểm thử tự động
├── run_server.py           # Launcher chính của ứng dụng
├── requirements.txt        # Danh sách thư viện Python
└── tailwind.config.js      # Cấu hình giao diện Tailwind
```

---

## 🚀 Hướng dẫn cài đặt & Chạy dự án (Getting Started)

### 1. Chuẩn bị môi trường
*   Cài đặt **Python 3.9** trở lên.
*   (Tùy chọn) Cài đặt **Node.js** nếu bạn muốn chỉnh sửa CSS (Tailwind).

### 2. Cài đặt thư viện
Mở terminal tại thư mục gốc và chạy:
```bash
pip install -r requirements.txt
```

### 3. Cấu hình biến môi trường
Sao chép file `.env.example` thành `.env`:
```bash
cp .env.example .env
```
*Lưu ý: Các thông tin nhạy cảm như mật khẩu DB sẽ được nhập trực tiếp khi khởi chạy để đảm bảo an toàn.*

### 4. Khởi chạy ứng dụng
Chạy script launcher:
```bash
python run_server.py
```
Hoặc dùng file bat trên Windows:
```bash
start_server.bat
```
*   **Bước 1:** Nhập mật khẩu để mở khóa/tạo Database (Mật khẩu cần độ phức tạp cao).
*   **Bước 2:** Nếu là lần đầu, hệ thống sẽ yêu cầu tạo tài khoản Admin.
*   **Bước 3:** Truy cập vào `http://127.0.0.1:8000` để bắt đầu làm việc.

---

## 🗺️ Kế hoạch phát triển (Roadmap)

Dựa trên cấu trúc hiện tại, hai hướng nâng cấp tiềm năng cho hệ thống bao gồm:

1.  **🔍 Tích hợp AI Search & Matching:** Áp dụng thuật toán Fuzzy logic nâng cao và xử lý ngôn ngữ tự nhiên (NLP) để tự động phát hiện các hồ sơ trùng lặp hoặc có mối quan hệ tiềm ẩn ngay cả khi dữ liệu đầu vào không đồng nhất.
2.  **📱 Mobile-First Dashboard:** Phát triển giao diện Dashboard tối ưu hóa hoàn toàn cho thiết bị di động và máy tính bảng, giúp cán bộ có thể tra cứu và rà soát hồ sơ nhanh chóng ngay tại hiện trường.

---
*Phát triển bởi đội ngũ Kỹ thuật - VCFE Project.*
