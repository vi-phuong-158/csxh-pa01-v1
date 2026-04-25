THÔNG TIN DỰ ÁN (PROJECT OVERVIEW)

Tên dự án: SECURITY PROFILE 360 (Hệ thống Quản trị An ninh PA01)

Mục tiêu: Refactor kiến trúc từ Monolith Streamlit sang mô hình Frontend-Backend phân tách (Server-rendered HTML + FastAPI).

Trạng thái: Chuyển đổi mã nguồn cũ. Nhánh làm việc hiện tại: claude/refactor-frontend-backend-split-fOOba.

Triết lý kiến trúc (Phương án A): Sử dụng FastAPI làm Backend API & Render Jinja2 Templates. Frontend sử dụng HTML thuần, Tailwind CSS, kết hợp HTMX để tương tác động (SPA-like) và Alpine.js cho UI state nhỏ. Tuyệt đối KHÔNG dùng các framework Frontend nặng (React/Vue).

TECH STACK CHUẨN (MANDATORY)

Backend: FastAPI, Uvicorn, Jinja2, Pydantic, python-multipart, itsdangerous.

Database: SQLAlchemy 2.x (ORM), sqlcipher3-binary (thay thế sqlite3 tiêu chuẩn để mã hóa file).

Frontend: Tailwind CSS (qua CLI build), HTMX, Alpine.js.

Thư viện UI: ECharts.js (Biểu đồ), DataTables.js (Bảng dữ liệu).

Caching & Utils: cachetools (thay thế @st.cache), python-dotenv.

QUY TẮC SỐNG CÒN CHO AI (AI GUARDRAILS - PHẢI TUÂN THỦ 100%)

1. Xóa bỏ hoàn toàn Streamlit (Eradicate Streamlit)

AI không được phép sử dụng bất kỳ hàm st.* nào trong backend mới (services, utils, db).

Thay thế @st.cache_data và @st.cache_resource bằng cachetools.TTLCache hoặc functools.lru_cache.

Thay thế st.secrets bằng pydantic-settings và file .env.

Thay thế st.session_state bằng cơ chế Server Session (FastAPI Session/Cookie) hoặc lưu trạng thái "Draft" vào Database.

2. Bảo mật Database & SQLCipher

Cốt lõi: Mã nguồn cũ dùng sqlite3 tiêu chuẩn khiến PRAGMA key không hoạt động. Bắt buộc thay đổi import từ sqlite3 sang from sqlcipher3 import dbapi2 as sqlite3.

Duy trì câu lệnh PRAGMA key=... để đảm bảo file DB được mã hóa toàn bộ.

3. Kiến trúc thư mục mục tiêu (Target Structure)

Mọi file tạo mới hoặc di chuyển phải tuân thủ cấu trúc sau:

csxh-pa01-v1/
├── backend/
│   ├── main.py (FastAPI app, mount static)
│   ├── config.py (Pydantic settings)
│   ├── deps.py (Dependencies: user, db, admin)
│   ├── security.py (Session, CSRF)
│   ├── routes/ (auth.py, dashboard.py, nhap_lieu.py,...)
│   ├── services/ (Logic nghiệp vụ tách khỏi UI)
│   ├── db/ (session.py, base.py)
│   ├── models/ (models.py giữ nguyên)
│   ├── schemas/ (Pydantic request/response)
│   └── utils/ (text_utils.py, fuzzy_matching.py,...)
├── frontend/
│   ├── templates/ (Jinja2: base.html, _partials/, auth/,...)
│   └── static/ (css/input.css, js/htmx, img/, uploads/)
├── tailwind.config.js
├── requirements.txt
└── .env


4. Quy tắc Frontend (HTMX & Tailwind)

Không viết CSS tùy chỉnh trừ khi thực sự cần thiết. Dùng 100% utility classes của Tailwind.

Các thao tác submit form, load tab, xóa item phải dùng HTMX (hx-get, hx-post, hx-target, hx-swap) thay vì viết Javascript fetch thuần.

Dùng Alpine.js (x-data, x-show, x-model) cho các thao tác ẩn hiện modal, tab, dropdown phía client.

LỘ TRÌNH THỰC THI (WORKFLOW & PHASES)

AI phải thực hiện tuần tự các bước dưới đây. Bắt buộc: Sau mỗi Phase, AI phải dừng lại, báo cáo kết quả và đợi người dùng xác nhận (Y/N) trước khi qua Phase tiếp theo.

Phase 0: Setup môi trường (Chuẩn bị)

Tạo file .env.example chứa DB_PASSWORD, SECRET_KEY, ADMIN_PASSWORD.

Cập nhật requirements.txt: Xóa streamlit, streamlit-echarts. Thêm fastapi, uvicorn, jinja2, python-multipart, itsdangerous, cachetools, sqlcipher3-binary, pydantic-settings.

Khởi tạo tailwind.config.js và tạo frontend/static/css/input.css. Thêm script build Tailwind vào package.json (nếu cần) hoặc hướng dẫn người dùng chạy npx.

Phase 1: Dọn dẹp Tầng Data & Service (Tách rễ Streamlit)

Hợp nhất logic của database.py và app/db/session.py vào backend/db/session.py.

QUAN TRỌNG: Sửa lại kết nối dùng from sqlcipher3 import dbapi2 as sqlite3 và thiết lập PRAGMA key.

Di chuyển services.py, app/services/* vào backend/services/.

Di chuyển utils/* vào backend/utils/.

Quét toàn bộ backend/services/ và backend/utils/: Xóa mọi import streamlit as st, thay thế @st.cache_* bằng cachetools.

Chạy thử các lệnh import python thuần để đảm bảo không còn dính dáng tới Streamlit.

Phase 2: Khung FastAPI & Authentication

Tạo backend/config.py đọc .env.

Tạo backend/main.py (FastAPI app, mount /static, setup Jinja2).

Tạo backend/security.py và backend/deps.py (quản lý Cookie/Session đăng nhập, JWT hoặc signed cookie).

Tạo backend/routes/auth.py (Login, Logout).

Xây dựng Frontend: frontend/templates/base.html (Layout chung với Tailwind) và frontend/templates/auth/login.html.
AI Checkpoint: Người dùng có thể chạy uvicorn backend.main:app và xem trang Đăng nhập trên trình duyệt.

Phase 3: Xây dựng Dashboard

Tạo backend/routes/dashboard.py trả về số liệu tổng quan.

Tạo frontend/templates/dashboard/index.html.

Tích hợp ECharts.js vào HTML, dùng Alpine.js hoặc Vanilla JS để fetch data từ API nội bộ hoặc render thẳng từ Jinja2.

Phase 4: Tra cứu & Rà soát (Chỉ đọc)

Tạo backend/routes/tra_cuu.py và backend/routes/ra_soat.py.

Thiết kế giao diện tra_cuu/index.html tích hợp DataTables.js để phân trang/sort phía client.

Chuyển đổi logic Fuzzy matching từ Utils sang endpoint phục vụ chức năng Rà soát bằng file Excel.

Phase 5: Giao diện Profile (View/Edit)

Tạo backend/routes/profile.py.

Thiết kế profile/index.html với cấu trúc Tabs (dùng Tailwind & Alpine.js).

Các tab phụ (Nhân thân, Liên hệ, Tài chính...) được load động bằng HTMX (hx-get).

Xử lý logic Upload File (Avatar, Tài liệu) qua endpoint multipart/form-data.

Phase 6: Chức năng Nhập liệu (Phức tạp nhất)

Lược bỏ cơ chế st.session_state staging cũ.

Thiết kế theo pattern "Draft & Commit": Khi bắt đầu nhập, tạo một bản ghi DoiTuong với cờ is_draft=True trong Database.

Giao diện nhap_lieu/index.html chia làm nhiều Tab. Các thao tác thêm Nhân thân/Phương tiện/v.v... sẽ lưu thẳng vào Database liên kết với bản ghi Draft.

Khi ấn "Hoàn tất", update cờ is_draft=False.

Phase 7: Bulk Import, Audit Log, User & Data Sources

Tạo các routes và templates tương ứng cho Quản lý User (Chỉ Admin).

Xây dựng trang hiển thị Audit Log (bảng phân trang).

Xây dựng chức năng Import Excel hàng loạt (Tái sử dụng logic cũ).

Phase 8 & 9: Hardening, Dọn dẹp & Test

Thêm CSRF token cho các form POST.

Cấu hình Rate Limit (Slowapi) cho endpoint Login.

Dọn dẹp các file .py của Streamlit cũ (app.py, thư mục views/ cũ).

Viết script chạy ứng dụng đơn giản (thay thế run_app.py).

[KẾT THÚC CLAUDE.md]