# 02 — Coding Rules

## 🚨 Guardrails sống còn (MANDATORY) — đọc trước khi chạm file

Vi phạm các quy tắc này làm hỏng hệ thống/lộ dữ liệu.

### [SEC-1] Bảo mật Database & SQLCipher
- **KHÔNG BAO GIỜ** `import sqlite3` chuẩn. Dùng `from sqlcipher3 import dbapi2 as sqlite3`.
- Engine SQLAlchemy phải truyền `module=sqlcipher3.dbapi2` (xem `db/session.py`), nếu không
  DB lưu plaintext.
- KHÔNG xóa/sửa lệnh `PRAGMA key=...`, `_verify_key`, `PRAGMA cipher_compatibility = 4`.
- Luôn dùng `NullPool` + `connect_args={"timeout": 30}` để tránh "database is locked".

### [ENV-1] Môi trường offline (localhost/LAN)
- App chạy `http://127.0.0.1:8000`, không HTTPS. Cookie `secure` bám theo `settings.USE_HTTPS`
  (mặc định False) — KHÔNG hardcode `secure=True`, login sẽ chết.
- **CSRF đã được BẬT toàn cục** (`Depends(csrf_protect)` ở app-level) — đừng gỡ. Đây là điểm
  KHÁC với ghi chú cũ "bỏ qua CSRF". Slowapi rate-limit chỉ là defense nội bộ, không cần lo
  quy mô cloud.

### [UI-1] Frontend & UX
- Chỉ HTMX (`hx-get`/`hx-post`/`hx-swap`) + Alpine.js. **KHÔNG** React/Vue/`fetch` thuần.
- Toast: dùng `HX-Trigger` từ backend → Alpine.js. **KHÔNG** `alert()`.
- Xác nhận xóa: modal Alpine.js. **KHÔNG** `confirm()` mặc định trình duyệt.
- Giữ nền glassmorphism: `bg-gradient-to-br from-emerald-50 via-white to-teal-50`, component
  `bg-white/70 backdrop-blur-md`. (Có thêm `cand-theme.css` cho theme ngành.)
- Tra cứu delay: `hx-trigger="keyup changed delay:500ms"`.

### [PKG-1] Đóng gói PyInstaller
- Đường dẫn đọc/ghi (`.db`, `data/uploads/`, `.env`) dùng runtime dir thật (`VCFE_RUNTIME_DIR`
  do `run_server.py` set), KHÔNG dùng `sys._MEIPASS`.

## Nguyên tắc chung (Karpathy)

- Viết ít nhất có thể để giải quyết đúng task. Không tính năng speculative.
- Không abstraction sớm: 3 đoạn lặp vẫn tốt hơn 1 abstraction non.
- Không xử lý lỗi cho kịch bản không thể xảy ra.
- Comment WHY, không comment WHAT. Không refactor code lân cận ngoài task.
- Suy nghĩ trước khi code: không giả định, nêu rõ đánh đổi, đề xuất phương án đơn giản trước.
- Theo mục tiêu: biến task thành tiêu chí xác minh được — [Bước] → [Kiểm tra].

## Style code

- Ngôn ngữ / runtime: **Python 3.10+** (backend), HTML/Jinja2 + Tailwind (frontend).
- Format: 4 space indent, `from __future__ import annotations` ở module mới, type hints
  SQLAlchemy 2.x (`Mapped[...]` / `mapped_column`). Docstring + comment **tiếng Việt** theo
  phong cách hiện có (nhiều file dùng mã rủi ro `F-xx` để truy vết).
- Linter / formatter: _(chưa cấu hình tự động — cần bổ sung; bám sát style file đang sửa)_

## Đặt tên

- Tên route/service/template/cột DB dùng **tiếng Việt không dấu, snake_case**
  (`tra_cuu`, `nhap_excel`, `doi_tuong`, `nguoi_phu_trach_id`). Giữ nguyên quy ước này.
- 1 router = 1 file trong `routes/`, kèm 1 file logic trong `services/` cùng tên khi cần.

## Bảo mật

- Secret (DB_PASSWORD, SECRET_KEY, ADMIN_PASSWORD) **không** đặt trong `.env`/source — nhập
  tương tác qua `run_server.py`, lưu keyring.
- Validate input ở backend (xem `utils/validators.py`, `validate_cccd`). Không tin client.
- Không log mật khẩu/khóa thô.
- Mọi thao tác đổi DB nên ghi `audit_log`.

## Không làm

- Không thêm dependency mới cho việc vài dòng (ưu tiên stdlib / thư viện đã có).
- Không đổi schema bằng tay — thêm cột/index qua `_PENDING_COLUMNS`/`_PENDING_INDEXES`.
- Không "sửa" module `bulk_import/` lung tung khi không có task rõ (xem KI-01 ở 03-decisions).

## Test

Chưa có bộ test tự động đầy đủ (đã cài `pytest`, `httpx`). Checklist thủ công tối thiểu:
- [ ] `python run_server.py` khởi động được, mở `http://127.0.0.1:8000`, đăng nhập OK.
- [ ] Thao tác đổi state (thêm/sửa/xóa) gửi kèm CSRF token, không lỗi 403.
- [ ] Sau khi thêm class Tailwind mới → đã build lại `output.css`.
- [ ] Không vi phạm [SEC-1]/[ENV-1] (không import sqlite3 chuẩn, không hardcode secure=True).

## Git

- Branch từ `main`, đặt tên rõ: `feat/...`, `fix/...`, `ui/...`, `docs/...`.
- Commit message ngắn, format `type: mô tả ngắn` (theo lịch sử: `ui:`, `perf+sec:`, `fix:`).
- Không push thẳng `main` nếu chưa được yêu cầu. Không `--force` push trừ khi được yêu cầu rõ.

## Nhắc về CSS build

Khi thêm class Tailwind mới, nhắc người dùng chạy:
```bash
npx tailwindcss -i ./frontend/static/css/input.css -o ./frontend/static/css/output.css
```
