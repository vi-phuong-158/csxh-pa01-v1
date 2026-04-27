# 🔍 Code Review: VCFE Database (csxh-pa01-v1)

Comprehensive review of the entire codebase. Findings sorted by severity.

---

## 🔴 Critical Issues

### 1. Dual Database Layer — Architectural Schizophrenia

The codebase has **two completely separate database access layers** that operate independently:

| Layer | Location | Tech | Used By |
|-------|----------|------|---------|
| **Raw SQLite** | [database.py](file:///d:/Code/csxh-pa01-v1/database.py) | `sqlite3` + `Row` factory | `views/`, [services.py](file:///d:/Code/csxh-pa01-v1/services.py), `views/profile/`, `views/audit_log.py`, `views/nguon_du_lieu.py`, `views/ra_soat.py` |
| **SQLAlchemy ORM** | [app/db/session.py](file:///d:/Code/csxh-pa01-v1/app/db/session.py) + [app/models/models.py](file:///d:/Code/csxh-pa01-v1/app/models/models.py) | `SQLAlchemy 2.0` with `Mapped` columns | `app/services/auth_service.py` only |

**Problems:**
- Two different connection pools, two different schemas  
- ORM models define relationships and constraints that raw SQL ignores  
- Schema drift risk: changing a column in `database.py`'s `init_db()` won't update the ORM model, and vice versa  
- `database.py` does its own `CREATE TABLE IF NOT EXISTS` while `app/init_db.py` calls `Base.metadata.create_all(engine)`

> [!CAUTION]
> If the ORM models evolve (e.g., adding a new column to `DoiTuong`), the raw `init_db()` in `database.py` won't know about it. This **will** cause silent data inconsistencies.

---

### 2. Connection Leak Patterns in `views/profile/getters.py`

Every getter function opens a connection and relies on `finally: conn.close()` — but `pd.read_sql_query()` can throw before the DataFrame is returned, and the `conn.close()` is **not** inside a try/finally in most functions:

```python
# getters.py — NO try/finally here
def get_lien_he_by_cccd(cccd):
    conn = get_connection()
    query = "SELECT * FROM lien_he WHERE cccd = ? ORDER BY created_at DESC"
    df = pd.read_sql_query(query, conn, params=(cccd,))
    conn.close()  # ← Skipped if read_sql_query throws
    return df
```

**Affected**: `get_lien_he_by_cccd`, `get_tai_chinh_by_cccd`, `get_phuong_tien_by_cccd`, `get_ho_so_dac_thu_by_cccd`, `get_tai_lieu_by_cccd`, `get_nhan_than_by_cccd`.

Only `get_doi_tuong_detail` and `get_file_path` use try/finally correctly.

---

### 3. Sensitive Data Exposure in Error Messages

```python
# nguon_du_lieu.py
except Exception as e:
    return False, f"Lỗi: {e}"  # raw exception goes to UI
```

```python
# auth_service.py
return False, f"Lỗi tạo tài khoản: {e}"
return False, f"Lỗi đổi mật khẩu: {e}"
```

Stack traces and internal database errors are propagated directly to `st.error()` in the UI.

---

## 🟠 High-Severity Issues

### 4. Dead Imports and Dead Code

| File | Dead Code |
|------|-----------|
| [auth.py](file:///d:/Code/csxh-pa01-v1/auth.py) | Entire 200+ line file. **All functions are duplicates** of `app/services/auth_service.py`. Used by exactly **zero** imports (verified by grep). |
| [database.py](file:///d:/Code/csxh-pa01-v1/database.py) L1 | `import os` — never used |
| [ra_soat.py](file:///d:/Code/csxh-pa01-v1/views/ra_soat.py) L420-421 | `import logging` inside exception handler (already imported at module level) |
| [app.py](file:///d:/Code/csxh-pa01-v1/app.py) L3 | `from pathlib import Path` — never used |
| [app.py](file:///d:/Code/csxh-pa01-v1/app.py) L11 | `from app.services.auth_service import is_super_admin` — imported but actually used from `views/login.py` separately |

> [!WARNING]
> `auth.py` (root level) is a **210-line dead file**. It duplicates `app/services/auth_service.py` entirely. No module imports from it. Delete it.

---

### 5. Admin Password Printed to stdout

```python
# auth_service.py:184-188
print("="*60)
print(f"[SECURITY NOTICE] Generated Random Super Admin Password")
print(f"Username: {DEFAULT_ADMIN_USERNAME}")
print(f"Password: {password}")
print("="*60)
```

In production (e.g., Docker), this password goes to container logs and can be harvested.

---

### 6. No CSRF / Session Token Protection

Login state is stored purely in `st.session_state.logged_in = True`. While Streamlit has some built-in protections, there is:
- No session expiry
- No session token rotation after login
- No idle timeout

---

## 🟡 Medium-Severity Issues

### 7. `database.py` Uses Global Lock but SQLite WAL May Suffice

```python
_db_lock = threading.Lock()
```

A Python-level threading lock is used, but `init_db()` already enables WAL mode (`PRAGMA journal_mode=WAL`). The lock serializes all writes unnecessarily. With WAL, SQLite supports concurrent readers and one writer without a Python-level lock.

### 8. Inconsistent Date Handling

- [database.py](file:///d:/Code/csxh-pa01-v1/database.py) stores `ngay_sinh` as `DATE` in raw SQL
- [models.py](file:///d:/Code/csxh-pa01-v1/app/models/models.py) maps it as `Mapped[Optional[datetime]]` with `Date` column type
- [nhap_lieu/ui.py](file:///d:/Code/csxh-pa01-v1/views/nhap_lieu/ui.py) converts dates with `str(...)` before insertion
- The profile view parses dates back with various methods

No consistent serialization/deserialization strategy exists.

### 9. No Input Validation on CCCD Beyond Length

The `validate_cccd` function in `services.py` only checks:
```python
if not cccd or len(cccd) != 12 or not cccd.isdigit():
```

No checksum validation. CCCD numbers in Vietnam have internal structure (province code, gender+century, sequence, checksum) that could be validated.

### 10. File Upload Path Traversal Risk

```python
# services.py:save_tai_lieu()
ten_file_luu = f"{cccd}_{uuid.uuid4().hex[:8]}_{uploaded_file.name}"
```

`uploaded_file.name` is user-controlled. While the UUID prefix helps, there's no sanitization of the filename. A malicious name like `../../etc/passwd` could be problematic on certain OS path joins.

### 11. `get_file_path()` Uses `Path.cwd()` for Path Resolution

```python
# getters.py:95
file_path = Path.cwd() / result[0]
```

This is fragile — if the working directory changes (e.g., running from a different path), all file paths break.

---

## 🟢 Low-Severity / Code Quality Issues

### 12. Redundant Absolute Import Paths

The app mixes relative and absolute imports inconsistently:
```python
from database import get_connection       # root-level module
from app.services.auth_service import ...  # app package
from views.profile import ...             # views package
from constants import ...                  # root-level module
```

No `__init__.py` at root level ties these together. The project appears to rely on Streamlit's working directory being the project root.

### 13. Hardcoded Magic Numbers

```python
# app.py
sidebar_width = 320  # hardcoded, also in CSS :root
```

```python
# services.py
MAX_UPLOAD_MB = 10  # also defined in constants.py as MAX_FILE_SIZE_MB = 10
```

### 14. No Tests

No test files, no test infrastructure, no `pytest.ini` or similar configuration.

### 15. Missing Type Hints on Most Functions

`auth_service.py` has type hints; the rest of the codebase has none (except occasional return type hints).

### 16. CSS `!important` Overuse

[style.css](file:///d:/Code/csxh-pa01-v1/style.css) uses `!important` extensively (~100+ occurrences). This is a maintenance nightmare — each new Streamlit version may require more `!important` overrides.

---

## 📋 Summary of Recommendations

| Priority | Action | Effort |
|----------|--------|--------|
| 🔴 P0 | Unify database layer: pick SQLAlchemy OR raw SQLite, not both | Large |
| 🔴 P0 | Fix connection leaks in `getters.py` (add try/finally) | Small |
| 🔴 P0 | Sanitize error messages shown to users | Small |
| 🟠 P1 | Delete dead `auth.py` file and dead imports | Small |
| 🟠 P1 | Stop printing passwords to stdout | Small |
| 🟠 P1 | Add session expiry / idle timeout | Medium |
| 🟡 P2 | Standardize date handling | Medium |
| 🟡 P2 | Sanitize uploaded filenames | Small |
| 🟡 P2 | Use absolute path config instead of `Path.cwd()` | Small |
| 🟢 P3 | Add basic test coverage | Large |
| 🟢 P3 | Clean up import structure | Medium |
