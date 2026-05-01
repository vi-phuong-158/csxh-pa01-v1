# Workflows — VCFE Database

> Tài liệu mô tả các luồng nghiệp vụ phức tạp để AI tái sử dụng đúng pattern.

---

## 1. Luồng Import Excel hàng loạt (`/nhap-excel/upload`)

**File:** `backend/routes/nhap_excel.py`

### Quy trình 4 bước

```
[1] Nhận file → [2] Đọc bằng pandas → [3] Validate từng dòng → [4] Insert theo chunk
```

### Bước 1: Nhận file (multipart)

```python
@router.post("/upload")
async def upload_excel(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "Chỉ chấp nhận file .xlsx hoặc .xls")
    content = await file.read()
```

### Bước 2: Đọc bằng pandas

```python
import pandas as pd
import io

df = pd.read_excel(io.BytesIO(content), dtype=str)  # dtype=str tránh pandas convert số
df.columns = df.columns.str.strip().str.lower()      # normalize tên cột

# Kiểm tra cột bắt buộc
required_cols = ['cccd', 'ho_ten']
missing = [c for c in required_cols if c not in df.columns]
if missing:
    return templates.TemplateResponse("nhap_excel/_results.html", {
        "request": request, "errors": [f"Thiếu cột: {', '.join(missing)}"],
        "success_count": 0, "fail_count": 0
    })
```

### Bước 3: Validate từng dòng

```python
errors = []
valid_rows = []

for idx, row in df.iterrows():
    row_num = idx + 2  # +2 vì Excel bắt đầu từ 1 và có header
    cccd = str(row.get('cccd', '')).strip()
    ho_ten = str(row.get('ho_ten', '')).strip()

    # Validate CCCD
    if not cccd or not re.match(r'^\d{9}$|^\d{12}$', cccd):
        errors.append({"row": row_num, "msg": f"CCCD không hợp lệ: '{cccd}'"})
        continue

    # Kiểm tra trùng trong DB
    if db.query(DoiTuong).filter(DoiTuong.cccd == cccd).first():
        errors.append({"row": row_num, "msg": f"CCCD {cccd} đã tồn tại"})
        continue

    # Parse ngày sinh (xử lý nhiều định dạng)
    ngay_sinh = None
    raw_date = row.get('ngay_sinh')
    if raw_date and str(raw_date).strip() not in ('', 'nan', 'NaT'):
        try:
            if isinstance(raw_date, (pd.Timestamp, datetime)):
                ngay_sinh = raw_date.date() if hasattr(raw_date, 'date') else raw_date
            else:
                ngay_sinh = datetime.strptime(str(raw_date).strip(), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            # Ngày không hợp lệ → bỏ qua, không báo lỗi cứng
            pass

    valid_rows.append({
        "cccd": cccd, "ho_ten": ho_ten.upper(),
        "ngay_sinh": ngay_sinh, ...
    })
```

### Bước 4: Insert theo chunk (tránh khóa SQLCipher)

```python
CHUNK_SIZE = 50
success_count = 0

for i in range(0, len(valid_rows), CHUNK_SIZE):
    chunk = valid_rows[i:i + CHUNK_SIZE]
    for data in chunk:
        obj = DoiTuong(**data, is_draft=False)
        db.add(obj)
    db.commit()  # commit mỗi chunk, không commit toàn bộ 1 lần
    success_count += len(chunk)

# Trả về partial HTML cho HTMX
return templates.TemplateResponse("nhap_excel/_results.html", {
    "request": request,
    "success_count": success_count,
    "fail_count": len(errors),
    "errors": errors,
})
```

**Lưu ý quan trọng:**
- **CHUNK_SIZE = 50**: SQLCipher có giới hạn transaction khi file lớn. Commit từng 50 dòng thay vì bulk insert toàn bộ.
- `dtype=str` khi đọc pandas: tránh bị pandas chuyển CCCD dạng `"012345678"` thành số `12345678`.
- Lỗi không cứng (soft error) với ngày sinh: ghi warning nhưng vẫn import dòng đó.
- Response trả về **partial HTML** (`_results.html`), không redirect.

---

## 2. Luồng Tạo Bản Nháp (Draft & Commit) — Nhập liệu mới

**File:** `backend/routes/nhap_lieu.py`, `backend/services/profile.py`

### Trạng thái của DoiTuong

```
[Tạo draft] → is_draft=True  →  [Nhập từng bước]  →  [Commit]  →  is_draft=False
     ↑                                                       ↓
  /nhap-lieu/start                                  /nhap-lieu/{cccd}/commit
```

### Bước 1: Tạo bản nháp

```python
# Route: POST /nhap-lieu/start
@router.post("/start")
async def start_nhap_lieu(request: Request, cccd: str = Form(...), db=Depends(get_db)):
    # Kiểm tra CCCD không tồn tại
    existing = db.query(DoiTuong).filter(DoiTuong.cccd == cccd).first()
    if existing:
        # Flash error, redirect về form
        ...

    # Tạo bản ghi nháp
    obj = DoiTuong(cccd=cccd, is_draft=True, created_at=datetime.now(), updated_at=datetime.now())
    db.add(obj)
    db.commit()

    # Redirect đến form nhập liệu
    return RedirectResponse(f"/nhap-lieu/{cccd}", status_code=303)
```

### Bước 2: Lưu thông tin cơ bản (auto-save)

```python
# Route: POST /nhap-lieu/{cccd}/save-basic
# Lưu thông tin nhưng GIỮ NGUYÊN is_draft=True
@router.post("/{cccd}/save-basic")
async def save_basic(cccd: str, request: Request, db=Depends(get_db), ...):
    data = await request.form()
    obj = db.query(DoiTuong).filter(DoiTuong.cccd == cccd, DoiTuong.is_draft == True).first()
    if not obj:
        raise HTTPException(404)
    # Update fields
    obj.ho_ten = str(data.get("ho_ten", "")).upper().strip()
    obj.updated_at = datetime.now()
    db.commit()
    # Trả về partial HTML (HTMX swap)
    response = templates.TemplateResponse("nhap_lieu/_save_success.html", {...})
    response.headers["HX-Trigger"] = json.dumps({"showToast": {"type": "success", "msg": "Đã lưu nháp"}})
    return response
```

### Bước 3: Hoàn tất (Commit)

```python
# Route: POST /nhap-lieu/{cccd}/commit
@router.post("/{cccd}/commit")
async def commit_nhap_lieu(cccd: str, db=Depends(get_db), ...):
    obj = db.query(DoiTuong).filter(DoiTuong.cccd == cccd, DoiTuong.is_draft == True).first()
    if not obj:
        raise HTTPException(404)
    if not obj.ho_ten:
        raise HTTPException(422, "Họ tên là bắt buộc trước khi hoàn tất")

    obj.is_draft = False
    obj.updated_at = datetime.now()
    db.commit()
    return RedirectResponse(f"/profile/{cccd}", status_code=303)
```

### Bước 4: Hủy bản nháp

```python
# Route: DELETE /nhap-lieu/{cccd}
# Xóa hoàn toàn bản ghi draft (và cascade xóa satellite data)
```

**Lưu ý:**
- Dữ liệu vệ tinh (thân nhân, liên hệ, v.v.) có thể được thêm vào bản nháp TRƯỚC khi commit.
- Khi query tìm bản nháp, **luôn filter cả `is_draft == True`** để không nhầm với hồ sơ đã hoàn tất.
- Hàm `commit_draft` cần validate ít nhất `ho_ten` không rỗng.

---

## 3. Luồng Rà soát tên (Fuzzy Matching) — `/ra-soat`

**File:** `backend/routes/ra_soat.py`, `backend/utils/fuzzy_matching.py`

```python
# Bước 1: Nhận file Excel, đọc cột 'ho_ten'
df = pd.read_excel(io.BytesIO(content), dtype=str)
input_names = df['ho_ten'].dropna().str.strip().tolist()

# Bước 2: Lấy toàn bộ tên trong DB (chỉ is_draft=False)
db_records = db.query(DoiTuong.cccd, DoiTuong.ho_ten)\
               .filter(DoiTuong.is_draft == False)\
               .all()
db_names = [(r.cccd, r.ho_ten) for r in db_records if r.ho_ten]

# Bước 3: Batch fuzzy matching
from backend.utils.fuzzy_matching import batch_screen
results = batch_screen(input_names, db_names, threshold=80)

# Bước 4: Trả partial HTML
return templates.TemplateResponse("ra_soat/_results.html", {
    "request": request, "results": results
})
```

**batch_screen trả về list dict:**
```python
{
    "input_name": "Nguyen Van A",
    "matched_cccd": "123456789",
    "matched_name": "NGUYỄN VĂN A",
    "score": 95,      # 0-100
    "quality": "high" # "high" >= 90, "medium" >= 80, "low" < 80
}
```

---

## 4. Luồng Upload File (Avatar / Tài liệu)

**File:** `backend/routes/profile.py`, `backend/security.py`

### Validate file upload (bắt buộc dùng)

```python
from backend.security import validate_upload_file, sanitize_filename
import magic  # python-magic
import uuid

async def upload_file_endpoint(cccd: str, file: UploadFile, kind: str):
    content = await file.read()

    # Validate: size + MIME (không tin extension)
    validate_upload_file(content, file.filename, kind)
    # kind = "avatar" → chỉ jpg/png/webp, max 5MB
    # kind = "document" → thêm pdf/doc/docx, max 5MB

    # Lưu với tên UUID để tránh path traversal
    ext = sanitize_filename(file.filename).rsplit('.', 1)[-1].lower()
    stored_name = f"{uuid.uuid4().hex}.{ext}"
    save_path = UPLOAD_DIR / kind / cccd / stored_name
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_bytes(content)
```

### Phục vụ file (authenticated only)

```
GET /api/documents/{kind}/{cccd}/{filename}
```
- Route này validate cccd regex + filename pattern trước khi serve.
- **Không dùng** `StaticFiles` trực tiếp cho thư mục `data/uploads/`.

---

## 5. Pattern ghi Audit Log

**Luôn gọi `_log()` khi thay đổi dữ liệu quan trọng:**

```python
from backend.services.profile import _log

# Trước khi update
old_data = {"ho_ten": obj.ho_ten, "gioi_tinh": obj.gioi_tinh}

# Thực hiện thay đổi
obj.ho_ten = new_ho_ten
db.commit()

# Sau khi update
new_data = {"ho_ten": obj.ho_ten, "gioi_tinh": obj.gioi_tinh}
_log(db, table="doi_tuong", action="UPDATE", key=cccd,
     old=old_data, new=new_data, user=current_user.username)
```

---

## 6. Pattern HTMX Response từ backend

```python
from fastapi.responses import HTMLResponse
import json

# Trả partial HTML + trigger toast
def htmx_response(html: str, toast_msg: str, toast_type: str = "success") -> HTMLResponse:
    resp = HTMLResponse(content=html)
    resp.headers["HX-Trigger"] = json.dumps({
        "showToast": {"type": toast_type, "msg": toast_msg}
    })
    return resp

# Redirect sau khi thành công (dùng cho form thường, không phải HTMX)
from fastapi.responses import RedirectResponse
return RedirectResponse(url=f"/profile/{cccd}", status_code=303)

# Trả lỗi dạng partial HTML (HTMX swap vào #error-area)
return HTMLResponse(
    content=f'<div class="text-error text-sm mt-2">{error_msg}</div>',
    status_code=422
)
```

---

## 7. Query DB chuẩn (SQLAlchemy 2.x)

```python
from sqlalchemy.orm import Session
from backend.db.session import get_db  # Dependency

# Select
obj = db.query(DoiTuong).filter(DoiTuong.cccd == cccd).first()
items = db.query(DoiTuong).filter(DoiTuong.is_draft == False).all()

# Insert
new_obj = DoiTuong(cccd="123456789", ho_ten="NGUYEN VAN A", is_draft=False)
db.add(new_obj)
db.commit()
db.refresh(new_obj)

# Update
obj.ho_ten = "NGUYEN VAN B"
obj.updated_at = datetime.now()
db.commit()

# Delete
db.delete(obj)
db.commit()

# Pagination
from sqlalchemy import func
total = db.query(func.count(DoiTuong.cccd)).scalar()
page_items = db.query(DoiTuong).offset((page-1)*page_size).limit(page_size).all()
```

---

## 8. Khởi động ứng dụng

```bash
# Build Tailwind CSS (bắt buộc sau khi sửa template)
npx tailwindcss -i frontend/static/css/input.css -o frontend/static/css/output.css --watch

# Chạy FastAPI
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Hoặc dùng script có sẵn
python run_server.py
```

**Biến môi trường cần có (file `.env`):**
```
DB_PATH=data/vcfe.db
DB_PASSWORD=your_db_password
SECRET_KEY=your_secret_key_min_32_chars
ADMIN_PASSWORD=your_admin_password
USE_HTTPS=false
```
