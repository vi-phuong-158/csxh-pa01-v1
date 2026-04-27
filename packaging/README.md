# Hướng Dẫn Đóng Gói QLNNN

## Tổng quan

Quy trình đóng gói gồm **5 bước** tạo ra file `QLNNN_Setup_v1.0.exe` **có chữ ký số**:

```
Bước 1: PyInstaller (One-Folder)  →  thư mục dist/QLNNN/
Bước 2: Ký số QLNNN.exe           →  exe có Authenticode signature
Bước 3: Inno Setup                →  dist/installer/QLNNN_Setup_v1.0.exe
Bước 4: Ký số installer           →  installer có Authenticode signature
Bước 5: Deploy cert lên máy user  →  Windows tin tưởng ứng dụng
```

> **Chạy `BUILD_APP.bat` để tự động hóa toàn bộ quy trình** (trừ Bước 5).

---

## Chuẩn bị một lần duy nhất

### 1. Cài Inno Setup

Tải miễn phí tại: <https://jrsoftware.org/isdl.php>  
→ Chọn **"innosetup-X.X.X.exe"** (bản ổn định mới nhất)

### 2. Tạo file icon

```bash
cd d:\Code\QLNNN-API
python packaging/convert_icon.py
```

→ Tạo ra `assets/logo.ico` từ `assets/logo.png`

### 3. Tạo chứng chỉ ký số (chỉ làm 1 lần)

> Bước này ngăn Windows SmartScreen/Defender chặn ứng dụng khi phân phối nội bộ.

Mở **PowerShell với quyền Administrator** rồi chạy:

```powershell
cd d:\Code\QLNNN-API
powershell -ExecutionPolicy Bypass -File packaging\setup_codesign.ps1
```

Script sẽ tạo ra:

- `packaging/QLNNN_codesign.pfx` — private key để ký (giữ bí mật, **không commit lên Git**)
- `packaging/QLNNN_codesign.cer` — public cert để cài lên máy người dùng

---

## Bước 1: Build bằng PyInstaller

```bash
cd d:\Code\QLNNN-API
python packaging/build.py
```

**Kết quả:** Thư mục `dist/QLNNN/` chứa toàn bộ ứng dụng  
**Thời gian:** Khoảng 3–7 phút lần đầu (lần sau nhanh hơn)

### Kiểm tra trước khi tiếp tục

Chạy thử file vừa build để đảm bảo hoạt động:
```bash
dist\QLNNN\QLNNN.exe
```

> ⚠️ **Quan trọng:** Phải test thành công Bước 1 trước khi làm Bước 2!

---

## Bước 2: Tạo bộ cài bằng Inno Setup

### Cách nhanh (GUI)
1. Mở **Inno Setup Compiler**
2. **File → Open** → chọn `packaging/installer.iss`
3. Nhấn **F9** (hoặc **Build → Compile**)
4. Đợi 1–2 phút

### Cách dòng lệnh (automation)
```bash
# Thay đường dẫn Inno Setup cho phù hợp máy bạn
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" packaging\installer.iss
```

**Kết quả:** File `dist/installer/QLNNN_Setup_v1.0.exe` (khoảng 80-150 MB)

---

## Cấu trúc file sau khi build

```
dist/
├── QLNNN/                    ← Thư mục One-Folder (Bước 1)
│   ├── QLNNN.exe             ← File chạy chính
│   ├── _internal/            ← Thư viện Python (tự động)
│   ├── frontend/             ← Giao diện web
│   ├── landing_page/         ← Trang landing
│   ├── assets/               ← Logo, hình ảnh
│   ├── nation.json           ← Dữ liệu quốc tịch
│   ├── .env.example          ← Template cấu hình
│   └── HUONG_DAN.txt         ← Hướng dẫn sử dụng
│
└── installer/
    └── QLNNN_Setup_v1.0.exe  ← BỘ CÀI ĐẶT CUỐI CÙNG (Bước 2)
```

---

## Lưu ý quan trọng

### File CSDL (.db) không đưa vào bộ cài
- File `qlnnn.db` **KHÔNG** được copy vào bộ cài (dữ liệu nhạy cảm!)
- Sau khi người dùng cài và chạy lần đầu → hệ thống tự tạo CSDL mới trống
- Nếu muốn chuyển dữ liệu cũ: sao chép thủ công `qlnnn.db` vào `{thư mục cài đặt}\backend\data\`

### File .env không đưa vào bộ cài
- Mật khẩu mã hóa CSDL không được nằm trong bộ cài
- Sau cài đặt, người dùng tạo file `.env` theo `.env.example`
- Hoặc hệ thống sẽ hỏi mật khẩu khi khởi động lần đầu

### sqlcipher3 (thư viện mã hóa SQLite)
- Thư viện này có native DLL → PyInstaller tự detect và copy
- Nếu gặp lỗi "DLL not found": copy thủ công `sqlcipher3.dll` từ thư mục Python

---

## Khắc phục lỗi thường gặp

| Lỗi | Nguyên nhân | Cách sửa |
|-----|-------------|----------|
| `ModuleNotFoundError: uvicorn` | Hidden import thiếu | Thêm vào `HIDDEN_IMPORTS` trong `build.py` |
| `WARNING: Hidden import not found` | Import khai báo sai tên | Kiểm tra lại tên module |
| App chạy nhưng không load được trang | Đường dẫn tĩnh sai | Kiểm tra `sys._MEIPASS` trong code |
| Inno Setup: "Source file not found" | Chưa chạy Bước 1 | Chạy `build.py` trước |

---

## Phân phối cho người dùng cuối (chống bị Windows chặn)

Sau khi build và ký số xong, người dùng cần được cài chứng chỉ tin cậy **một lần**
trước khi chạy ứng dụng. Có hai cách:

### Cách 1: Chạy script trên từng máy (Admin)

Sao chép file `packaging/QLNNN_codesign.cer` lên máy người dùng, rồi chạy:

```powershell
powershell -ExecutionPolicy Bypass -File "deploy_cert.ps1"
```

### Cách 2: Triển khai hàng loạt qua Group Policy (GPO)

Trong **Group Policy Management Console** trên Domain Controller:

```text
Computer Configuration
  → Windows Settings
    → Security Settings
      → Public Key Policies
        → Trusted Publishers   ← import QLNNN_codesign.cer vào đây
        → Trusted Root CA      ← import QLNNN_codesign.cer vào đây cũng
```

Sau đó GPO sẽ tự đẩy cert đến tất cả máy trong domain.

---

## Cập nhật phiên bản mới

1. Sửa `#define AppVersion` trong `installer.iss` và `version_info.txt`
2. Chạy lại `BUILD_APP.bat` (đã tự động ký và tạo installer)
3. Phân phối file `dist/installer/QLNNN_Setup_vX.X.X.exe` mới
