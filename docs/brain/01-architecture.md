# 01 — Architecture

## Stack

| Layer | Công nghệ |
|-------|-----------|
| Frontend | HTML + Jinja2, Tailwind CSS (CLI build), HTMX (partial reload/SPA), Alpine.js (state/modal/tab), ECharts (biểu đồ), DataTables |
| Backend | FastAPI, Uvicorn, Pydantic v2 / pydantic-settings, SQLAlchemy 2.x (ORM), slowapi (rate-limit), bcrypt + itsdangerous (auth), pandas/openpyxl (Excel), rapidfuzz (fuzzy), fpdf2 + python-docx (export) |
| Database | SQLCipher (AES-256) qua `sqlcipher3-binary`; một file `.db` (mặc định `security_profile.db`) |
| Hạ tầng / Hosting | 100% offline — Uvicorn tại `http://127.0.0.1:8000`. Đóng gói `.exe` bằng PyInstaller |
| Khác | keyring (Windows Credential Manager) lưu mật khẩu DB; PBKDF2-SHA256 sinh `SECRET_KEY` từ `DB_PASSWORD` |

## Cấu trúc thư mục chính

```
csxh-pa01-v1/
├── run_server.py            # ★ Launcher: nhập/keyring mật khẩu, set env, kill port, mở browser, chạy uvicorn
├── build_app.bat           # Đóng gói .exe (PyInstaller)
├── requirements.txt
├── .env / .env.example     # CHỈ cờ vận hành (DEBUG, USE_HTTPS, DB_NAME, UPLOAD_DIR, PORT) — KHÔNG chứa secret
├── backend/
│   ├── main.py             # Entry FastAPI: middleware CSRF cookie, mount static, include 16 router
│   ├── config.py           # Settings (pydantic-settings) — fail-fast validate secret
│   ├── deps.py             # Dependencies: get_current_user/require_login/require_admin, csrf_protect, require_profile_access
│   ├── security.py         # session token, csrf token, hash bcrypt
│   ├── limiter.py          # slowapi limiter
│   ├── constants.py
│   ├── db/
│   │   ├── session.py      # ★ Engine SQLCipher (NullPool, PRAGMA key), get_db, init_db, auto-migrate
│   │   └── base.py         # Declarative Base
│   ├── models/models.py    # ★ Toàn bộ schema ORM
│   ├── routes/             # Handler HTTP (trả Jinja2 partial cho HTMX hoặc JSON cho ECharts)
│   ├── services/           # Logic nghiệp vụ (search, auth, profile, network, events, dashboard, docx_export, nhap_excel)
│   └── utils/              # text_utils (bỏ dấu), validators, fuzzy_matching, deduplication, security_utils, bulk_import/(*KI-01 dead*)
└── frontend/
    ├── templates/          # base.html + components/ + _partials/ + thư mục theo tính năng
    └── static/             # css/(input,output,cand-theme), js/vendor/(htmx,alpine,echarts,jquery,datatables), js/app/
```

## Code Graph (bản đồ module)

> Cập nhật lại MỖI KHI thay đổi cấu trúc/quan hệ phụ thuộc.

### Module/file then chốt

| Module / file | Vai trò | Được gọi bởi | Phụ thuộc vào |
|---------------|---------|--------------|---------------|
| `run_server.py` | Launcher: nhập mật khẩu (getpass/GUI/keyring), set env var, kill port, mở browser, `uvicorn.run` | người dùng / `.exe` | `backend.main:app`, keyring, sqlcipher3 |
| `backend/main.py` | Tạo `app`, middleware cookie CSRF, mount `/static`, include 16 router, redirect `/`→`/dashboard` | `run_server` | `config`, `db.session`, `deps`, `limiter`, `security`, `routes/*` |
| `backend/config.py` | `settings` đọc env + validate fail-fast (DB_PASSWORD≥12, SECRET_KEY≥32) | gần như **mọi** module | pydantic-settings, env vars |
| `backend/db/session.py` | Engine SQLCipher (`module=sqlcipher3`, NullPool, `PRAGMA key`+verify, WAL), `get_db`, `init_db`, `_auto_migrate` | `main`, mọi `routes`/`services` cần DB | `config`, `models.models`, `utils.text_utils` |
| `backend/db/base.py` | `Base` declarative | `models.models`, `session` | SQLAlchemy |
| `backend/models/models.py` | Toàn bộ bảng ORM (DoiTuong + vệ tinh + hệ thống) | `services/*`, `deps`, `session` | `db.base` |
| `backend/deps.py` | Auth + CSRF + phân quyền hồ sơ (Depends) | mọi `routes/*` | `config`, `db.session`, `models`, `security`, `utils.validators` |
| `backend/security.py` | Ký/verify session token & CSRF token, bcrypt | `deps`, `services.auth`, `main` | `config`, itsdangerous, bcrypt |
| `backend/routes/*` | 1 router/tính năng; trả HTML partial (HTMX) hoặc JSON (ECharts) | `main` | `deps`, `db.session`, `services/*`, Jinja2 |
| `backend/services/*` | Logic nghiệp vụ thuần, nhận `Session` | `routes/*` tương ứng | `models`, `utils/*` |
| `backend/utils/text_utils.py` | `remove_accents` — dùng cả trong hàm SQL `unaccent_lower` | `session`, `services.search`, fuzzy | — |

### Luồng xử lý chính

```
Browser (HTMX hx-get/hx-post + header X-CSRF-Token)
  → backend/main.py  (csrf_cookie_middleware + Depends csrf_protect toàn cục)
  → routes/<feature>.py  (Depends require_login / require_admin / require_profile_access)
  → services/<feature>.py  (logic nghiệp vụ)
  → get_db() → Session (SQLCipher engine, NullPool, PRAGMA key mỗi connect)
  → trả về: Jinja2 partial HTML  ──► HTMX hx-swap vào DOM
             (+ header HX-Trigger ──► Alpine.js bật Toast)
         hoặc JSON ──► ECharts render biểu đồ
```

## Mô hình dữ liệu / API

**Bảng lõi `doi_tuong`** (PK = `cccd` dạng String). Các bảng vệ tinh FK `cccd`
(`ondelete=CASCADE`), quan hệ `cascade="all, delete-orphan"`:
`lien_he`, `tai_chinh`, `phuong_tien`, `nhan_than`, `ho_so_dac_thu`, `tai_lieu`,
`qua_trinh_hoat_dong`.

**Bảng hệ thống:** `quan_he_doi_tuong` (cạnh đồ thị: `cccd_1`↔`cccd_2`, `loai_quan_he`,
`do_tin_cay`), `nguon_du_lieu`, `audit_log`, `cccd_history` (tra CCCD cũ↔mới), `users`
(`role` ∈ {`user`,`super_admin`}, lockout, `must_change_password`).

**Auto-migrate** (idempotent) trong `db/session.py`: thêm cột mới qua `_PENDING_COLUMNS`,
thêm index qua `_PENDING_INDEXES` (`create_all` KHÔNG tự ALTER bảng cũ). Khi thêm cột/index
mới → append vào hai list này, KHÔNG sửa bảng bằng tay.

**Router (16, prefix tiêu biểu):** `auth` `/auth`, `dashboard` `/dashboard`, `tra_cuu`
`/tra-cuu`, `ra_soat`, `profile`, `quan_he`, `network`, `nhap_lieu`, `quan_ly_user`,
`audit_log`, `nguon_du_lieu`, `nhap_excel`, `danh_ba`, `bao_cao`, `files`, `events`.
Pattern: `GET ""` trả trang index; `GET/POST "/api/..."` trả partial/JSON. Mọi route đổi
trạng thái tự động bị `csrf_protect` kiểm tra.

## Biến môi trường

```
# Secret — nhập tương tác qua run_server.py (KHÔNG đặt trong .env):
DB_PASSWORD        # ≥12 ký tự, có cả chữ và số; mở khóa file SQLCipher
SECRET_KEY         # ký session; tự sinh từ DB_PASSWORD (PBKDF2) — không nhập tay
ADMIN_PASSWORD     # chỉ hỏi lần đầu khi DB chưa có user

# Cờ vận hành — đọc từ .env (an toàn để commit .env.example):
DEBUG              # default false
USE_HTTPS          # default false → cookie secure=False cho HTTP localhost
DB_NAME            # default security_profile.db
UPLOAD_DIR         # default data/uploads (nên NGOÀI frontend/static)
PORT               # default 8000
VCFE_RUNTIME_DIR   # do run_server.py set — thư mục ghi dữ liệu thật (cho .exe)
```

## Lưu ý kiến trúc quan trọng

- **SQLCipher ≠ sqlite3 chuẩn:** phải truyền `module=sqlcipher3.dbapi2` vào `create_engine`,
  nếu không SQLAlchemy dùng `sqlite3` stdlib → `PRAGMA key` vô hiệu → DB lưu **plaintext**.
  `PRAGMA cipher_compatibility = 4` được PIN để DB mở được qua các bản SQLCipher 4/5.
- **NullPool + `PRAGMA key` mỗi connect:** không connection nào "rò" mà thiếu key; `timeout=30`
  tránh "database is locked". Có `_verify_key` fail-fast nếu mật khẩu sai (chống fail-open).
- **CSRF bật toàn cục** (app-level `Depends(csrf_protect)`): mọi POST/PUT/PATCH/DELETE cần
  header `X-CSRF-Token` (HTMX) hoặc field `_csrf`. Middleware tự set cookie `csrf_token`
  (httponly=False) trên mọi GET trang HTML.
- **Phân quyền hồ sơ** (`require_profile_access`): super_admin xem tất cả; user thường chỉ xem
  hồ sơ `nguoi_phu_trach_id == user.id` hoặc hồ sơ chưa phân công (NULL).
- **Nhập Excel phải chunk** (50–100 dòng/commit) để tránh lock — quy tắc CLAUDE; lưu ý KI-01
  hiện chưa tuân thủ đầy đủ.
- **PyInstaller:** dữ liệu ghi (`.db`, `data/uploads`) dùng `VCFE_RUNTIME_DIR` (cạnh `.exe`),
  KHÔNG dùng `sys._MEIPASS` (thư mục tạm read-only).
