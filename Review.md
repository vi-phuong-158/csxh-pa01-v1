# Review Dự Án: VCFE Database v2.0

> Ngày review: 2026-05-18  
> Reviewer: Claude Sonnet 4.6 (AI Code Review)  
> Nhánh: `main`

---

## Tổng Quan Dự Án

**VCFE Database** là hệ thống quản lý hồ sơ nội bộ chạy hoàn toàn offline/LAN, được xây dựng cho đơn vị PA01 - Công an tỉnh Phú Thọ. Mục đích: lưu trữ, tra cứu và phân tích thông tin về người Việt Nam có yếu tố nước ngoài.

**Kiến trúc tổng thể:**
```
run_server.py (Launcher)
    └─> FastAPI (backend/) + Jinja2/HTMX/Alpine.js (frontend/)
            └─> SQLCipher AES-256 (security_profile.db)
```

---

## Đánh Giá Tổng Thể

| Hạng mục | Điểm | Nhận xét |
|----------|------|----------|
| Bảo mật | 9/10 | CSRF, rate limit, mã hóa DB, audit log, phân quyền |
| Kiến trúc | 8/10 | Phân tách routes/services/models rõ ràng |
| Chất lượng code | 8/10 | Nhất quán, tuân thủ CLAUDE.md |
| UX/Giao diện | 8/10 | Glassmorphism nhất quán, HTMX mượt mà |
| Bảo trì (Maintainability) | **6/10** | Có module chết và import sai thế hệ |

---

## Điểm Mạnh

- **SQLCipher AES-256**: File `.db` mã hóa toàn bộ — lấy cắp file không đọc được
- **NullPool + PRAGMA key**: Đặt key mỗi request, tránh "Database is locked"  
- **CSRF stateless**: Token ký bằng `SECRET_KEY`, không cần session store
- **Fail-fast config**: Pydantic validate ngay khi khởi động, sai thì crash sớm
- **Audit Log**: Mọi thao tác đọc/ghi đều được ghi lại, có thể truy vết
- **Account lockout**: 5 lần sai → khóa 5 phút, tránh brute force

---

## Vấn Đề Quan Trọng Cần Khắc Phục

---

### VẤN ĐỀ 1 (Nghiêm trọng): Module `bulk_import` là Dead Code hoàn toàn

Đây là vấn đề phức tạp nhất trong dự án. Có **hai implementation cạnh tranh nhau** cho tính năng nhập Excel, và cả hai đều không hoàn chỉnh.

#### 1a. Cấu trúc thư mục bị lồng sai

```
Hiện tại (SAI):
backend/utils/bulk_import/              ← KHÔNG có __init__.py
    └── bulk_import/                     ← lồng thêm 1 cấp thừa
        ├── __init__.py
        ├── constants.py
        ├── exporters.py
        ├── importers.py
        ├── templates.py
        └── validators.py

Đúng phải là:
backend/utils/bulk_import/              ← có __init__.py
    ├── constants.py
    ├── exporters.py
    ├── importers.py
    ├── templates.py
    └── validators.py
```

**Hệ quả**: Outer folder `utils/bulk_import/` không có `__init__.py` nên Python không nhận ra đây là package. Import sẽ thất bại hoàn toàn với `ModuleNotFoundError`.

#### 1b. Import sai thế hệ (Streamlit → FastAPI migration chưa hoàn tất)

`importers.py` và `validators.py` vẫn dùng cú pháp kết nối DB từ thời Streamlit cũ:

```python
# importers.py dòng 6 — SAI (module này không tồn tại trong FastAPI project)
from database import get_connection

# validators.py dòng 7 — SAI (tương tự)
from database import get_connection

# constants.py dòng 5 — SAI (không phải backend.constants)
from constants import DANH_SACH_XA_PHU_THO, GIOI_TINH_OPTIONS, ...
```

Trong khi đó, FastAPI project hiện tại dùng:
```python
# Cách đúng với SQLAlchemy ORM
from backend.db.session import get_db
from sqlalchemy.orm import Session
```

**Hệ quả**: Nếu ai cố import `bulk_import`, sẽ báo lỗi `ModuleNotFoundError: No module named 'database'` ngay lập tức.

#### 1c. Route `nhap_excel.py` không dùng module trên

Thay vì sử dụng `bulk_import`, route `nhap_excel.py` có **implementation riêng inline** (dòng 39–133) với nhiều giới hạn:

| Tính năng | `utils/bulk_import/` (chết) | `nhap_excel.py` (đang dùng) |
|-----------|----------------------------|------------------------------|
| Đọc nhiều sheet | Có (7 sheets) | Không (chỉ 1 sheet) |
| Validate đầy đủ | Có (CCCD, tỉnh, xã, nghề nghiệp) | Tối giản (chỉ check cccd + ho_ten) |
| Quan hệ nhân thân | Có (graph + satellite) | Không |
| Chunked commit | Không | Không (1 commit cho tất cả) |
| Deduplication | Có | Không |

**Chunked commit vi phạm CLAUDE.md**: Route hiện tại commit toàn bộ `N` dòng trong một lần (dòng 121):
```python
# nhap_excel.py dòng 121 — NGUY HIỂM với file lớn
db.commit()  # Commit 1000 dòng cùng lúc → "Database is locked"
```
CLAUDE.md yêu cầu: *"Phải xử lý insert theo từng chunk 50-100 dòng một lần commit"*.

---

#### Cách khắc phục (theo thứ tự ưu tiên)

**Bước 1 — Sửa cấu trúc thư mục:**
```
# Di chuyển các file từ inner folder ra outer folder
backend/utils/bulk_import/
    __init__.py   ← tạo mới (copy từ inner/__init__.py)
    constants.py
    exporters.py
    importers.py
    templates.py
    validators.py
```
Sau đó xóa thư mục `backend/utils/bulk_import/bulk_import/`.

**Bước 2 — Cập nhật import trong `importers.py`:**
```python
# Xóa:
from database import get_connection

# Thêm:
from sqlalchemy.orm import Session
from backend.models.models import DoiTuong, LienHe, TaiChinh, PhuongTien, NhanThan

# Đổi chữ ký hàm:
def bulk_import_all(validated_data: dict, db: Session, ...) -> tuple:
    # Dùng db.add() + db.flush() thay vì cursor.executemany()
```

**Bước 3 — Cập nhật import trong `validators.py`:**
```python
# Xóa:
from database import get_connection

# Thêm:
from sqlalchemy.orm import Session
from backend.models.models import DoiTuong

# Đổi chữ ký hàm:
def validate_excel_data(excel_file, db: Session, ...) -> dict:
    existing_cccds = {row.cccd for row in db.query(DoiTuong.cccd).all()}
```

**Bước 4 — Sửa import constants:**
```python
# Xóa:
from constants import DANH_SACH_XA_PHU_THO, ...

# Thêm:
from backend.constants import DANH_SACH_XA_PHU_THO, ...
```

**Bước 5 — Thêm chunked commit vào `importers.py`:**
```python
CHUNK_SIZE = 50

def bulk_import_all(validated_data: dict, db: Session) -> tuple:
    records = build_record_list(validated_data)  # list of ORM objects
    
    for i in range(0, len(records), CHUNK_SIZE):
        chunk = records[i : i + CHUNK_SIZE]
        db.add_all(chunk)
        db.commit()  # Commit mỗi 50 dòng
    
    return True, f"Import thành công {len(records)} bản ghi", stats
```

**Bước 6 — Kết nối `nhap_excel.py` với module:**
```python
# nhap_excel.py — thay inline code bằng:
from backend.utils.bulk_import import validate_excel_data, bulk_import_all

@router.post("/upload")
async def upload_excel(file, user, db):
    validated = validate_excel_data(file, db)
    ok, msg, stats = bulk_import_all(validated, db)
    return templates.TemplateResponse(...)
```

---

### VẤN ĐỀ 2 (Nhỏ): Hệ quả đổi mật khẩu DB chưa được document

`SECRET_KEY` được tạo ra từ `DB_PASSWORD` qua PBKDF2. Nếu admin đổi mật khẩu DB:
- `SECRET_KEY` mới ≠ `SECRET_KEY` cũ
- **Tất cả session đang hoạt động bị vô hiệu hóa ngay lập tức**
- Cán bộ đang đăng nhập sẽ bị kick ra không báo trước

Khắc phục: Thêm thông báo trong hướng dẫn sử dụng hoặc trong GUI lúc đổi mật khẩu.

---

### VẤN ĐỀ 3 (Nhỏ): `schemas/` folder trống

```
backend/schemas/__init__.py  ← chỉ có file này, không có Pydantic schemas
```

Dự án chưa có Pydantic response/request schemas. Hiện tại các route trả về trực tiếp từ ORM models. Điều này ổn cho hệ thống internal, nhưng nếu sau này thêm API JSON public thì cần bổ sung.

---

## Tóm Tắt Ưu Tiên Việc Cần Làm

| Độ ưu tiên | Việc cần làm | File liên quan |
|-----------|--------------|----------------|
| P1 — Gấp | Sửa cấu trúc `bulk_import/` và import sai | `utils/bulk_import/**` |
| P1 — Gấp | Thêm chunked commit vào nhập Excel | `routes/nhap_excel.py` |
| P1 — Gấp | Kết nối route với module `bulk_import` | `routes/nhap_excel.py` |
| P2 — Nên | Document hệ quả đổi mật khẩu DB | README, hướng dẫn |
| P3 — Tùy | Bổ sung Pydantic schemas nếu cần API JSON | `schemas/` |

---

## Kết Luận

Dự án có nền móng bảo mật rất vững chắc và kiến trúc rõ ràng. Vấn đề duy nhất đáng lo ngại là module `bulk_import` — một tính năng quan trọng đã được xây dựng khá hoàn chỉnh nhưng **bị ngắt khỏi hệ thống** trong quá trình chuyển đổi từ Streamlit sang FastAPI, dẫn đến dead code và tính năng nhập Excel hiện tại hoạt động ở mức tối giản. Khắc phục vấn đề này sẽ nâng mức độ hoàn thiện của hệ thống lên đáng kể.
