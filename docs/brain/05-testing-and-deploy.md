# 05 — Testing & Deploy

> Mọi lệnh để dựng môi trường, chạy, test, build, deploy. Agent đọc đây thay vì đoán lệnh.

## Cài đặt môi trường local

Yêu cầu **Python 3.10+** (và Node.js nếu cần build lại Tailwind).

```bash
pip install -r requirements.txt
npm install                 # chỉ cần nếu sẽ build lại Tailwind CSS
```

Biến môi trường:
- **Secret KHÔNG đặt trong `.env`.** `DB_PASSWORD` nhập tương tác khi chạy (lưu keyring);
  `SECRET_KEY` tự sinh từ `DB_PASSWORD`; `ADMIN_PASSWORD` chỉ hỏi lần đầu.
- `.env` (tùy chọn, copy từ `.env.example`) chỉ chứa cờ vận hành:
```
DEBUG=false
USE_HTTPS=false
DB_NAME=security_profile.db
UPLOAD_DIR=data/uploads
PORT=8000
```

## Chạy local (dev)

```bash
python run_server.py
```
- Hộp thoại GUI (hoặc getpass nếu không có tkinter) hỏi mật khẩu DB; lần đầu hỏi tạo admin.
- Tự kill tiến trình chiếm port, tự mở trình duyệt.

Truy cập: **http://127.0.0.1:8000** (PORT mặc định 8000; README nhắc tới 9000 — giá trị thật
lấy theo `PORT` trong `.env`, code default 8000).

## Build CSS (khi thêm class Tailwind mới)

```bash
npx tailwindcss -i ./frontend/static/css/input.css -o ./frontend/static/css/output.css
```

## Build (production / đóng gói .exe)

```bash
build_app.bat              # PyInstaller → dist/VCFED/... (xem build/VCFED.spec)
```
Chạy `.exe` trong `dist/` — dữ liệu ghi (`.db`, `data/uploads`) nằm cạnh `.exe`
(`VCFE_RUNTIME_DIR`), KHÔNG trong thư mục tạm `_MEIPASS`.

## Test

Đã cài `pytest`, `httpx` nhưng **chưa có bộ test tự động đầy đủ** _(cần bổ sung)_.

```bash
pytest                     # nếu/khi có thư mục tests/
```

Checklist thủ công trước khi commit/push:
- [ ] `python run_server.py` lên được, đăng nhập OK tại `http://127.0.0.1:8000`.
- [ ] Thao tác thêm/sửa/xóa gửi kèm CSRF token (không 403); xóa qua modal Alpine, không `confirm()`.
- [ ] Tra cứu/danh bạ/fuzzy trả kết quả; partial HTMX swap đúng; Toast hiển thị qua HX-Trigger.
- [ ] Nếu thêm class Tailwind → đã build lại `output.css`.
- [ ] Không vi phạm [SEC-1] (sqlcipher3, PRAGMA key) và [ENV-1] (không hardcode secure=True).

## Deploy

Không có deploy server. "Deploy" = đóng gói `.exe` bằng `build_app.bat` rồi copy bộ
`dist/VCFED/` sang máy đích; chạy offline trên Windows.

## Môi trường

| Môi trường | Branch | URL |
|-----------|--------|-----|
| Production (.exe trên máy nghiệp vụ) | `main` | http://127.0.0.1:8000 |
| Local (dev) | — | http://127.0.0.1:8000 |

## Lưu ý

- Đổi `DB_PASSWORD` → đổi `SECRET_KEY` → mọi session bị đăng xuất (KI-02).
- Sai mật khẩu DB → keyring tự xóa, hỏi lại; file DB không mở được nếu sai key (fail-fast).
- WAL được checkpoint khi tắt êm (atexit); tắt cứng có thể để lại file `-wal`.
