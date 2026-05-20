BỘ NÃO ĐIỀU PHỐI DỰ ÁN VCFE DATABASE

Trạng thái: ĐANG REFACTOR GIAO DIỆN — Chuyển từ Glassmorphism sang Paper CAND Theme.
Branch: feature/ui-cand-refresh | Pha 0-3 HOÀN THÀNH, chuẩn bị Pha 4.

1. TỔNG QUAN DỰ ÁN (PROJECT OVERVIEW)

Tên dự án: VCFE Database (Cơ sở dữ liệu về người Việt Nam có yếu tố nước ngoài - PA01 Phú Thọ).

Môi trường hoạt động: 100% Offline / Localhost / LAN. Chạy qua file đóng gói .exe (PyInstaller).

Kiến trúc: Frontend-Backend phân tách nhưng chạy chung một tiến trình Uvicorn.

Triết lý UX/UI: Sang trọng, nghiêm trang. Phong cách Paper CAND — nền giấy kem sáng, banner đỏ CAND, viền vàng gold, watermark trống đồng. File override: `cand-theme.css` load SAU `output.css`.

2. TECH STACK (CÔNG NGHỆ BẮT BUỘC)

Backend: FastAPI, Uvicorn, Jinja2, Pydantic, pandas hoặc openpyxl (xử lý file Excel).

Database: sqlcipher3-binary (Tuyệt đối quan trọng: Mã hóa AES-256 toàn bộ file DB), SQLAlchemy 2.x (ORM).

Frontend: HTML thuần, Tailwind CSS (qua CLI build), HTMX (Xử lý SPA, Partial reload), Alpine.js (Xử lý State UI, Modal, Tabs).

Đóng gói (Packaging): PyInstaller (qua file build_app.bat và launcher.py).

3. 🚨 QUY TẮC SỐNG CÒN CHO AI (MANDATORY GUARDRAILS) 🚨

AI đọc kỹ các quy tắc này trước khi chạm vào bất kỳ file nào. Vi phạm sẽ làm hỏng hệ thống.

[SEC-1] BẢO MẬT DATABASE & SQLCIPHER:

KHÔNG BAO GIỜ import sqlite3 tiêu chuẩn. BẮT BUỘC dùng: from sqlcipher3 import dbapi2 as sqlite3.

KHÔNG ĐƯỢC xóa lệnh PRAGMA key=....

Để tránh lỗi "Database is locked" khi xử lý bất đồng bộ, luôn dùng NullPool với connect_args={"timeout": 30} cho SQLAlchemy engine.

[ENV-1] MÔI TRƯỜNG OFFLINE (LOCALHOST):

Ứng dụng chạy trên http://127.0.0.1:8000. KHÔNG thiết lập secure=True cho Cookie đăng nhập (vì không có HTTPS), nếu không chức năng Login sẽ chết.

Bỏ qua các cảnh báo bảo mật về CSRF hay Rate Limiting dành cho Cloud, vì đây là hệ thống Local/LAN nội bộ khép kín.

[UI-1] QUY TẮC FRONTEND & UX:

Không Framework JS Nặng: Tuyệt đối KHÔNG dùng React, Vue hay viết JS thuần fetch API. Mọi thao tác gọi API phải dùng HTMX (hx-get, hx-post, hx-swap).

Thông báo (Toast): Luôn dùng HX-Trigger từ Backend để kích hoạt Toast Notification phía Frontend qua Alpine.js. KHÔNG dùng alert().

Xác nhận (Confirm): Mọi thao tác Xóa phải dùng Modal của Alpine.js, KHÔNG dùng confirm() mặc định của trình duyệt.

Giao diện Paper CAND: Nền giấy kem var(--paper), card trắng var(--card), banner đỏ var(--cand-red), chữ vàng var(--cand-gold). Override toàn bộ class dark cũ (bg-slate-*, text-slate-*) qua phần LEGACY OVERRIDE trong `cand-theme.css`.

[PKG-1] ĐÓNG GÓI PYINSTALLER:

Mọi đường dẫn đọc/ghi file (như .env, .db, thư mục uploads/) phải dùng đường dẫn tuyệt đối dựa trên vị trí thực thi thực tế, không dùng đường dẫn tạm của PyInstaller (sys._MEIPASS).

4. CẤU TRÚC THƯ MỤC CỐT LÕI (DIRECTORY STRUCTURE)

Bám sát cấu trúc sau khi thêm tính năng:

csxh-pa01-v1/
├── backend/
│   ├── main.py        # Entry point FastAPI, cấu hình CORS, tĩnh
│   ├── config.py      # Đọc biến môi trường từ .env
│   ├── routes/        # Chứa API Endpoints (auth, profile, dashboard...)
│   ├── services/      # Logic nghiệp vụ (CRUD, tính toán, import Excel)
│   ├── db/            # session.py (SQLCipher NullPool), base.py
│   ├── models/        # SQLAlchemy Models (Schema DB)
│   └── schemas/       # Pydantic schemas (Request/Response)
├── frontend/
│   ├── templates/     # HTML Jinja2 (base.html, _partials/...)
│   └── static/        # css/input.css, js/ (htmx, alpine, echarts)
├── launcher.py        # Script chạy server & tự mở trình duyệt
├── build_app.bat      # Script đóng gói ra file .exe
├── tailwind.config.js
└── requirements.txt



5. QUY TRÌNH NÂNG CẤP TÍNH NĂNG (WORKFLOW)

Khi User yêu cầu thêm tính năng mới, AI phải thực hiện theo vòng lặp sau:

Plan (Lập kế hoạch): Đọc kỹ Database Models xem đã có bảng dữ liệu chưa. In ra kế hoạch triển khai (Cần sửa route nào, template nào) và chờ User đồng ý.

Backend First: Viết/Sửa schemas -> Viết services -> Viết routes. Đảm bảo trả về HTML Partial (cho HTMX) hoặc JSON (cho ECharts).

Frontend Second: Viết giao diện HTML, gán các class Tailwind Kính mờ, tích hợp thẻ hx-* của HTMX và x-data của Alpine.js.

CSS Build Reminder: Luôn nhắc User phải tự chạy lệnh npx tailwindcss -i ./frontend/static/css/input.css -o ./frontend/static/css/output.css nếu có thêm class Tailwind mới.

Verify (Tự kiểm tra): Soát lại xem có vi phạm quy tắc [SEC-1] và [ENV-1] không trước khi báo cáo hoàn thành.

6. LỘ TRÌNH PHÁT TRIỂN TIẾP THEO (ROADMAP)

Các tính năng đang được ưu tiên triển khai:

Mục tiêu HIỆN TẠI: REFACTOR GIAO DIỆN CAND THEME (xem chi tiết tại REFACTOR_UI_PLAN.md)
- Pha 0 (Chuẩn bị): HOÀN THÀNH
- Pha 1 (Login + Dashboard): HOÀN THÀNH
- Pha 2 (Shell: base + sidebar + banner): HOÀN THÀNH
- Pha 2B (CSS Polish toàn cục): HOÀN THÀNH
- Pha 3 (Trang nghiệp vụ: tra_cuu, nhap_lieu, nhap_excel, danh_ba): HOÀN THÀNH
- Pha 4-6: CHƯA BẮT ĐẦU

Mục tiêu SAU REFACTOR: Phát triển tính năng Nhập liệu từ file Excel (Bulk Import)

Backend: Xây dựng endpoint nhận file multipart/form-data. Sử dụng pandas hoặc openpyxl để parse dữ liệu.

Database Safety: Phải xử lý insert theo từng "chunk" (ví dụ: 50-100 dòng một lần commit) để tránh lỗi "Database is locked".

Frontend: Giao diện Upload File (kéo thả) với Tailwind, có Progress Bar (nếu có thể) và thông báo bằng Toast (Thành công bao nhiêu dòng, lỗi dòng nào).

Tính năng tiếp theo: Danh bạ Tra cứu SĐT và Số tài khoản Ngân hàng toàn cục (Tận dụng cơ chế Delay Search của HTMX: hx-trigger="keyup changed delay:500ms").

Tính năng tương lai 1: Báo cáo Thống kê chuyên sâu (Dùng ECharts.js, lọc biểu đồ theo thời gian thực không reload trang).

Tính năng tương lai 2: Xuất báo cáo ra định dạng Excel/Word tự động từ dữ liệu tìm kiếm.

7. NGUYÊN TẮC LẬP TRÌNH CỦA KARPATHY (KARPATHY CODING GUIDELINES)
 
Triết lý để giảm thiểu sai lầm khi lập trình với AI, tập trung vào sự đơn giản và chính xác.
 
[KCG-1] Tư Duy Trước Khi Code (Think Before Coding):
- Đừng giả định: Luôn làm rõ các giả định. Nếu không chắc chắn, hãy hỏi lại.
- Minh bạch: Nếu có nhiều cách giải quyết, hãy liệt kê và phân tích đánh đổi (tradeoffs).
- Đề xuất phương án đơn giản: Nếu có cách đơn giản hơn, hãy đề xuất trước khi bắt tay vào làm.
 
[KCG-2] Ưu Tiên Sự Đơn Giản (Simplicity First):
- Tối giản: Chỉ viết code tối thiểu cần thiết để giải quyết vấn đề. Không thêm tính năng "dự phòng".
- Không trừu tượng hóa sớm: Đừng tạo ra các lớp trừu tượng (abstractions) cho code chỉ dùng một lần.
- Kiểm thử "Senior": Tự đặt câu hỏi: "Một kỹ sư cấp cao có thấy đoạn code này quá phức tạp không?"
 
[KCG-3] Chỉnh Sửa Chính Xác (Surgical Changes):
- Chỉ chạm vào những gì cần thiết: Không tự ý "cải thiện" code xung quanh, comment hoặc định dạng không liên quan.
- Đồng bộ style: Tuân thủ tuyệt đối phong cách code hiện có trong file.
- Dọn dẹp gọn gàng: Chỉ xóa những gì là hệ quả của thay đổi hiện tại.
 
[KCG-4] Thực Thi Theo Mục Tiêu (Goal-Driven Execution):
- Tiêu chí thành công: Biến nhiệm vụ thành các mục tiêu có thể kiểm chứng (ví dụ: "Viết test lỗi -> Sửa cho pass").
- Kế hoạch từng bước: Với tác vụ phức tạp, hãy nêu kế hoạch: [Bước] -> Kiểm tra: [Kết quả].
 
[KẾT THÚC CLAUDE.md]
