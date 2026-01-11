🛠️ TASK 1: QUY HOẠCH HẠ TẦNG (Setup)

Mục tiêu: Tạo cấu trúc thư mục và di chuyển file tiện ích.

Tôi đang có một dự án Streamlit viết tất cả trong 1 file `app.py` (root folder). Tôi muốn tái cấu trúc lại (Refactor) để theo mô hình Modular.
Hãy thực hiện các việc sau giúp tôi:

1.  Tạo thư mục mới tên là `views`.
2.  Trong thư mục `views`, tạo file `__init__.py` rỗng.
3.  Tạo thư mục mới tên là `utils`.
4.  Trong thư mục `utils`, tạo file `__init__.py` rỗng.
5.  Di chuyển file `bulk_import.py` từ thư mục gốc vào trong thư mục `utils/`.
6.  Sửa nội dung file `utils/bulk_import.py`: Cập nhật lại các dòng import (ví dụ: `from database import...` hoặc `from constants import...`) để đảm bảo nó vẫn tìm thấy các module ở thư mục gốc. Nên sử dụng absolute imports nếu có thể.

Kết quả mong đợi: Hiển thị cây thư mục sau khi thay đổi và code file `utils/bulk_import.py` đã sửa.


📊 TASK 2: DI LÝ DASHBOARD & NHẬP LIỆU

Mục tiêu: Tách 2 chức năng cơ bản nhất ra khỏi app.py.

Tiếp tục Refactor. Hãy tách code logic từ file `app.py` gốc sang các file mới trong thư mục `views`.
Lưu ý: Chỉ trích xuất code, KHÔNG thay đổi logic nghiệp vụ.

1.  **Tạo file `views/dashboard.py`**:
    -   Tìm hàm `page_dashboard()` trong `app.py`.
    -   Di chuyển hàm này và các hàm phụ trợ (như `get_statistics`, `get_recent_records`) sang file này.
    -   Thêm các import cần thiết (`streamlit`, `plotly`, `pandas`, `database`, `datetime`...) vào đầu file.

2.  **Tạo file `views/nhap_lieu.py`**:
    -   Tìm hàm `page_nhap_lieu()` trong `app.py`.
    -   Di chuyển hàm này và các hàm xử lý form (`save_doi_tuong`, `save_lien_he`, `save_tai_lieu`...) sang file này.
    -   Đảm bảo import đủ `database` và các hằng số từ `constants.py` (`DANH_SACH_XA_PHU_THO`, `GIOI_TINH_OPTIONS`...).

Kết quả mong đợi: Code đầy đủ của `views/dashboard.py` và `views/nhap_lieu.py`.


🔍 TASK 3: DI LÝ TRA CỨU & RÀ SOÁT

Mục tiêu: Tách các chức năng nghiệp vụ phức tạp.

Tiếp tục tách các chức năng còn lại từ `app.py` sang thư mục `views`:

1.  **Tạo file `views/tra_cuu.py`**:
    -   Chuyển hàm `page_tra_cuu()` sang file này.

2.  **Tạo file `views/ho_so_chi_tiet.py`**:
    -   Chuyển hàm `page_profile_view(cccd)` và các hàm lấy dữ liệu chi tiết (`get_doi_tuong_detail`, `get_lien_he_by_cccd`...) sang file này.

3.  **Tạo file `views/ra_soat.py`**:
    -   Chuyển hàm `page_ra_soat()` và `process_batch_screening` sang file này.

4.  **Tạo file `views/nhap_excel.py`**:
    -   Chuyển hàm `page_nhap_excel()` sang file này.
    -   **Lưu ý:** Cập nhật import `bulk_import` thành `from utils import bulk_import`.

Kết quả mong đợi: Code đầy đủ cho 4 file trên. Chú ý xử lý các lệnh `import` chính xác.


🎮 TASK 4: THIẾT LẬP BỘ CHỈ HUY (Main Router)

Mục tiêu: Viết lại app.py thành file điều hướng gọn nhẹ.

Bây giờ, hãy viết lại hoàn toàn file `app.py` ở thư mục gốc. File này sẽ đóng vai trò là Router điều hướng.

**Yêu cầu nội dung `app.py` mới:**
1.  Giữ lại cấu hình `st.set_page_config` và load CSS (`style.css`).
2.  Giữ lại Sidebar menu.
3.  Import các views đã tách:
    `from views import dashboard, nhap_lieu, nhap_excel, tra_cuu, ra_soat, ho_so_chi_tiet`
4.  Dựa vào lựa chọn ở Sidebar (radio button), gọi hàm `page_...()` tương ứng từ các module trên.
5.  **Quan trọng:** Giữ lại logic xử lý `st.session_state`:
    -   Nếu `st.session_state.get('view_profile_cccd')` có dữ liệu -> Gọi `ho_so_chi_tiet.page_profile_view(...)`.
    -   Ngược lại -> Hiển thị trang theo Menu Sidebar.

Kết quả mong đợi: Code trọn vẹn của file `app.py` mới (khoảng dưới 150 dòng).


✅ TASK 5: NGHIỆM THU & LIÊN KẾT

Mục tiêu: Đảm bảo các file nhìn thấy nhau và chạy ổn định.

Bước cuối cùng:

1.  Hãy tạo nội dung cho file `views/__init__.py`. Mặc dù để trống cũng được, nhưng hãy export các hàm chính ra để file `app.py` import gọn hơn.
    Ví dụ: `from .dashboard import page_dashboard` ...
    Để trong `app.py` tôi chỉ cần viết: `from views import page_dashboard, page_nhap_lieu...`

2.  Hãy liệt kê danh sách các thư viện cần cài đặt (nếu có thay đổi trong `requirements.txt`) hoặc các lưu ý đặc biệt khi chạy app với cấu trúc mới này.

Kết quả mong đợi: Nội dung `views/__init__.py` và `app.py` (phiên bản import tối ưu).
