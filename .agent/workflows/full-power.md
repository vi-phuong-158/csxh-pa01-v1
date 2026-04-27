---
description: Chạy các lệnh phát triển với toàn quyền (không cần hỏi)
---

// turbo-all

Sử dụng workflow này để thực hiện các tác vụ phát triển mà không cần xác nhận thủ công.

### 1. Cài đặt môi trường
Chạy lệnh này để cài đặt các package cần thiết:
```bash
pip install -r requirements.txt
```

### 2. Chạy ứng dụng Streamlit
Khởi động giao diện quản lý:
```bash
streamlit run app.py
```

### 3. Import dữ liệu mẫu
Chạy script import dữ liệu:
```bash
python bulk_import.py
```

### 4. Kiểm tra Database
Chạy script kiểm tra cơ sở dữ liệu:
```bash
python database.py
```
