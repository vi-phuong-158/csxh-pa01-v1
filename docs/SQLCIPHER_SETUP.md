# Hướng dẫn thiết lập SQLCipher cho Security Profile 360

## 📌 Tổng quan

**SQLCipher** là một extension mã hóa toàn bộ cơ sở dữ liệu SQLite ở mức **AES-256-CBC**. Sau khi cài đặt, file `security_profile.db` sẽ hoàn toàn là dữ liệu mã hóa – không thể đọc được nếu không có mật khẩu.

> **Tại sao cần?**  
> Khi cài đặt dạng portable trên laptop, nếu máy tính bị mất hoặc bị truy cập trái phép, dữ liệu nhạy cảm trong file `.db` có thể bị đọc trực tiếp bằng bất kỳ trình SQLite nào. SQLCipher giải quyết vấn đề này.

---

## 🔧 Tùy chọn cài đặt

### Tùy chọn 1: Sử dụng `pysqlcipher3` (Khuyên dùng cho Python)

```bash
# Cài đặt trên Windows (cần Visual C++ Build Tools)
pip install pysqlcipher3

# Hoặc dùng bản pre-built wheel (nếu có)
pip install pysqlcipher3 --only-binary=:all:
```

> ⚠️ **Lưu ý Windows**: `pysqlcipher3` yêu cầu biên dịch từ source. Bạn cần:
> - [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
> - [OpenSSL](https://slproweb.com/products/Win32OpenSSL.html) (Win64 OpenSSL v3.x)
> - Thiết lập biến môi trường `OPENSSL_DIR`, `OPENSSL_INCLUDE_DIR`, `OPENSSL_LIB_DIR`

### Tùy chọn 2: Sử dụng `sqlcipher3` (đơn giản hơn)

```bash
pip install sqlcipher3-binary
```

> Gói `sqlcipher3-binary` đi kèm binary pre-built nên **không cần biên dịch**.

### Tùy chọn 3: Sử dụng SQLAlchemy + SQLCipher

```bash
pip install sqlcipher3-binary
# SQLAlchemy đã hỗ trợ dialect: sqlite+pysqlcipher://
```

---

## 🔀 Hướng dẫn tích hợp vào dự án

### Bước 1: Cài đặt package

```bash
pip install sqlcipher3-binary
```

### Bước 2: Sửa file `app/db/session.py`

Thay đổi connection string để dùng SQLCipher:

```python
# === TRƯỚC (SQLite thuần) ===
# from sqlalchemy import create_engine
# engine = create_engine("sqlite:///security_profile.db")

# === SAU (SQLCipher) ===
from sqlalchemy import create_engine, event

# Mật khẩu mã hóa database
# ⚠️ KHÔNG hardcode trong production - dùng biến môi trường!
import os
DB_PASSWORD = os.environ.get("DB_ENCRYPTION_KEY", "your-secure-passphrase-here")

engine = create_engine(
    f"sqlite+pysqlcipher://:{DB_PASSWORD}@/security_profile.db",
    module=__import__("sqlcipher3"),  # Trỏ tới sqlcipher3 module
)
```

### Bước 3: Sửa file `database.py` (Legacy SQLite module)

```python
# === TRƯỚC ===
# import sqlite3
# conn = sqlite3.connect(get_db_path())

# === SAU ===
import sqlcipher3 as sqlite3  # Drop-in replacement

DB_PASSWORD = os.environ.get("DB_ENCRYPTION_KEY", "your-secure-passphrase-here")

def get_connection():
    conn = sqlite3.connect(get_db_path())
    conn.execute(f"PRAGMA key = '{DB_PASSWORD}'")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode=WAL")
    return conn
```

### Bước 4: Thiết lập mật khẩu mã hóa

Tạo file `.env` trong thư mục gốc dự án:

```env
# .env - KHÔNG commit file này vào Git!
DB_ENCRYPTION_KEY=Mat-Khau-Bao-Mat-Cuc-Manh-2026!@#
```

Cập nhật `.gitignore`:

```gitignore
# Database encryption key
.env
```

### Bước 5: Mã hóa database hiện có

Nếu đã có file `security_profile.db` chưa mã hóa, cần chuyển đổi:

```python
"""
Script chuyển đổi SQLite -> SQLCipher
Chạy 1 lần duy nhất để mã hóa database hiện có.
"""
import sqlcipher3 as sqlite3
import os
import shutil

DB_PATH = "security_profile.db"
DB_PASSWORD = os.environ.get("DB_ENCRYPTION_KEY", "your-secure-passphrase-here")

# 1. Backup database gốc
shutil.copy2(DB_PATH, f"{DB_PATH}.backup_before_encryption")
print(f"✅ Đã backup: {DB_PATH}.backup_before_encryption")

# 2. Mở database gốc (chưa mã hóa)
conn = sqlite3.connect(DB_PATH)

# 3. Attach một database mới có mã hóa
conn.execute(f"ATTACH DATABASE 'encrypted_{DB_PATH}' AS encrypted KEY '{DB_PASSWORD}'")

# 4. Export toàn bộ dữ liệu sang database mã hóa
conn.execute("SELECT sqlcipher_export('encrypted')")

# 5. Đóng kết nối
conn.execute("DETACH DATABASE encrypted")
conn.close()

# 6. Thay thế database gốc bằng database mã hóa
os.replace(f"encrypted_{DB_PATH}", DB_PATH)
print(f"✅ Đã mã hóa thành công: {DB_PATH}")

# 7. Kiểm tra
conn = sqlite3.connect(DB_PATH)
conn.execute(f"PRAGMA key = '{DB_PASSWORD}'")
cursor = conn.execute("SELECT count(*) FROM doi_tuong")
count = cursor.fetchone()[0]
print(f"✅ Xác nhận: {count} bản ghi đối tượng có thể đọc được")
conn.close()
```

---

## 🛡️ Bảo mật mật khẩu mã hóa

### Phương án 1: Biến môi trường (Khuyên dùng)

```powershell
# Windows - Thiết lập biến môi trường hệ thống
[System.Environment]::SetEnvironmentVariable("DB_ENCRYPTION_KEY", "Mat-Khau-Cuc-Manh!", "User")

# Hoặc chỉ trong session hiện tại
$env:DB_ENCRYPTION_KEY = "Mat-Khau-Cuc-Manh!"
```

### Phương án 2: File cấu hình riêng

Dùng `python-dotenv` (đã có trong `requirements.txt`):

```python
# Thêm vào đầu file app.py hoặc run_app.py
from dotenv import load_dotenv
load_dotenv()  # Tự động đọc file .env
```

### Phương án 3: Nhập từ bàn phím khi khởi động

```python
import getpass
DB_PASSWORD = getpass.getpass("Nhập mật khẩu mã hóa database: ")
```

> 💡 Phương án này an toàn nhất cho portable deployment trên laptop.

---

## ⚠️ Lưu ý quan trọng

1. **MẬT KHẨU = CHÌA KHÓA**: Nếu mất mật khẩu, dữ liệu **KHÔNG THỂ khôi phục**. Hãy ghi lại mật khẩu ở nơi an toàn.

2. **Backup script cần cập nhật**: File `scripts/backup_db.py` cũng cần thêm `PRAGMA key` khi đọc database đã mã hóa.

3. **Performance**: SQLCipher làm chậm khoảng 5-15% so với SQLite thuần (do mã hóa/giải mã). Với lượng dữ liệu nhỏ (<100MB), ảnh hưởng không đáng kể.

4. **Tương thích**: Các công cụ SQLite thông thường (DB Browser, DBeaver) **không thể** mở file đã mã hóa. Cần dùng phiên bản hỗ trợ SQLCipher (ví dụ: [DB Browser for SQLite with SQLCipher](https://sqlitebrowser.org/)).

5. **Windows Defender**: Một số antivirus có thể cảnh báo khi ứng dụng đọc/ghi file mã hóa. Hãy thêm thư mục dự án vào whitelist.

---

## 📋 Checklist triển khai

- [ ] Cài đặt `sqlcipher3-binary` 
- [ ] Tạo file `.env` với `DB_ENCRYPTION_KEY`
- [ ] Cập nhật `.gitignore` để không commit `.env`
- [ ] Sửa `app/db/session.py` (SQLAlchemy)
- [ ] Sửa `database.py` (Legacy connections)
- [ ] Chạy script mã hóa database hiện có
- [ ] Cập nhật `scripts/backup_db.py` để hỗ trợ database mã hóa
- [ ] Test lại ứng dụng hoàn chỉnh
- [ ] Kiểm tra backup/restore hoạt động với database mã hóa
- [ ] Ghi lại mật khẩu ở nơi an toàn (offline)

---

## 📚 Tham khảo

- [SQLCipher Official](https://www.zetetic.net/sqlcipher/)
- [sqlcipher3-binary on PyPI](https://pypi.org/project/sqlcipher3-binary/)
- [SQLAlchemy SQLCipher Dialect](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#pysqlcipher)
- [DB Browser for SQLite](https://sqlitebrowser.org/)
