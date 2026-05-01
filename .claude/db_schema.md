# DB Schema — VCFE Database

> Trích xuất từ `backend/models/models.py`. Cập nhật lần cuối: 2026-05-01.
> Database file: SQLCipher (mã hóa AES-256). Kết nối bắt buộc dùng `from sqlcipher3 import dbapi2 as sqlite3`.

---

## Bảng chính: `doi_tuong`

| Cột | Kiểu | Nullable | Ghi chú |
|-----|------|----------|---------|
| `cccd` | String | NOT NULL | **PK**. CMND/CCCD/Hộ chiếu (9–12 chữ số) |
| `ho_ten` | String | nullable | Indexed. **Lưu dạng UPPERCASE** (service tự convert) |
| `ngay_sinh` | Date | nullable | Format: `date` object Python / `YYYY-MM-DD` khi nhập string |
| `gioi_tinh` | String | nullable | Indexed. Enum: `"Nam"`, `"Nữ"` |
| `dia_chi_tinh` | String | nullable | Default: `"Phú Thọ"` |
| `dia_chi_xa` | String | nullable | Indexed. Xã/phường trong tỉnh Phú Thọ |
| `anh_chan_dung` | String | nullable | Đường dẫn file avatar (relative to UPLOAD_DIR) |
| `phan_loai_nghe_nghiep` | String | nullable | Indexed. Xem enum bên dưới |
| `chi_tiet_nghe_nghiep` | String | nullable | Mô tả chi tiết nghề nghiệp |
| `ghi_chu_chung` | Text | nullable | Ghi chú tổng |
| `is_draft` | Boolean | NOT NULL | Default: `False`. `True` = bản nháp chưa hoàn tất |
| `nguoi_phu_trach_id` | Integer | nullable | **FK** → `users.id` (SET NULL on delete). Indexed |
| `created_at` | DateTime | NOT NULL | Auto-set |
| `updated_at` | DateTime | NOT NULL | Auto-update |

**Relationships (cascade delete-orphan):**
- `lien_he` → `LienHe[]`
- `tai_chinh` → `TaiChinh[]`
- `phuong_tien` → `PhuongTien[]`
- `nhan_than` → `NhanThan[]`
- `ho_so_dac_thu` → `HoSoDacThu[]`
- `tai_lieu` → `TaiLieu[]`
- `qua_trinh` → `QuaTrinhHoatDong[]`

---

## Bảng vệ tinh (đều có `cccd` FK → `doi_tuong.cccd`, CASCADE DELETE)

### `lien_he` — Liên hệ
| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `id` | Integer PK | Auto |
| `cccd` | String FK | |
| `loai_lien_he` | String | Enum: SĐT, Email, Facebook, Zalo, Telegram, Instagram, Tiktok, Khác |
| `gia_tri` | String | Giá trị liên hệ (số điện thoại, email, v.v.) |
| `ghi_chu` | Text | |
| `created_at` | DateTime | |

### `tai_chinh` — Tài khoản ngân hàng
| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `id` | Integer PK | |
| `cccd` | String FK | |
| `ngan_hang` | String | Xem danh sách 18 ngân hàng trong constants.py |
| `so_tai_khoan` | String | |
| `chu_tai_khoan` | String | |
| `ghi_chu` | Text | |
| `created_at` | DateTime | |

### `phuong_tien` — Phương tiện
| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `id` | Integer PK | |
| `cccd` | String FK | |
| `loai_xe` | String | Enum: 7 loại xe |
| `bien_kiem_soat` | String | Biển số xe |
| `ten_phuong_tien` | String | Tên/nhãn hiệu xe |
| `ghi_chu` | Text | |
| `created_at` | DateTime | |

### `nhan_than` — Thân nhân
| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `id` | Integer PK | |
| `cccd` | String FK | |
| `loai_quan_he` | String | **NOT NULL**. Loại quan hệ (Vợ/Chồng, Bố/Mẹ, Con, v.v.) |
| `ho_ten` | String | |
| `cccd_nhan_than` | String | CCCD của thân nhân (nếu có) |
| `ngay_sinh` | Date | |
| `gioi_tinh` | String | Default: `""` |
| `dia_chi_tinh` | String | Default: `""` |
| `dia_chi_xa` | String | Default: `""` |
| `nghe_nghiep` | String | |
| `noi_o` | Text | Địa chỉ thường trú |
| `ghi_chu` | Text | |
| `created_at` | DateTime | |

### `ho_so_dac_thu` — Hồ sơ đặc thù
| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `id` | Integer PK | |
| `cccd` | String FK | |
| `loai_hinh` | String | **NOT NULL**. Xem enum bên dưới |
| `noi_dung_chi_tiet` | Text | |
| `ghi_chu` | Text | |
| `created_at` | DateTime | |
| `updated_at` | DateTime | |

**Enum `loai_hinh`:**
- `Hon_Nhan_NN` — Kết hôn với người nước ngoài
- `Lam_Viec_NN` — Làm việc cho tổ chức nước ngoài
- `Hoc_Tap_Cong_Tac_NN` — Học tập/công tác nước ngoài
- `Vi_Pham_NN` — Vi phạm pháp luật nước ngoài
- `Xac_Minh` — Đã xác minh

### `tai_lieu` — Tài liệu đính kèm
| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `id` | Integer PK | |
| `cccd` | String FK | |
| `ten_file_goc` | String | Tên file gốc sau sanitize |
| `ten_file_luu` | String | Tên lưu trên disk (UUID) |
| `duong_dan` | String | Đường dẫn relative to UPLOAD_DIR |
| `loai_tai_lieu` | String | 9 loại — xem constants.py |
| `mo_ta` | Text | |
| `dung_luong` | Integer | Bytes |
| `dinh_dang` | String | Extension (jpg, pdf, v.v.) |
| `created_at` | DateTime | |

### `qua_trinh_hoat_dong` — Quá trình hoạt động
| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `id` | Integer PK | |
| `cccd` | String FK | |
| `thoi_gian` | String | Diễn giải khoảng thời gian (text) |
| `ngay_bat_dau` | Date | Indexed |
| `ngay_ket_thuc` | Date | Indexed. Dùng để tính sự kiện sắp hết hạn |
| `noi_dung` | Text | |
| `ghi_chu` | Text | |
| `created_at` | DateTime | |

---

## Bảng hệ thống

### `users` — Người dùng hệ thống
| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `id` | Integer PK | |
| `username` | String UNIQUE | |
| `password_hash` | String | Bcrypt |
| `ho_ten` | String | |
| `role` | String | Default: `"user"`. Enum: `"super_admin"`, `"user"` |
| `is_active` | Integer | Default: 1 |
| `must_change_password` | Integer | Default: 0 |
| `failed_login_attempts` | Integer | Default: 0 |
| `lockout_until` | DateTime | nullable. Khóa tài khoản sau 5 lần thất bại |
| `created_at` | DateTime | |
| `last_login` | DateTime | nullable |

### `audit_log` — Nhật ký thao tác
| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `id` | Integer PK | |
| `bang` | String | Tên bảng bị tác động |
| `hanh_dong` | String | `INSERT`, `UPDATE`, `DELETE` |
| `khoa_chinh` | String | Giá trị PK (cccd hoặc id) |
| `du_lieu_cu` | Text | JSON cũ (nullable) |
| `du_lieu_moi` | Text | JSON mới (nullable) |
| `nguoi_thuc_hien` | String | Username |
| `ip_address` | String | |
| `created_at` | DateTime | |

### `nguon_du_lieu` — Nguồn dữ liệu
| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `id` | Integer PK | |
| `ten_nguon` | String NOT NULL | |
| `loai_nguon` | String | |
| `thoi_gian_import` | DateTime | |
| `nguoi_import` | String | |
| `file_goc` | String | |
| `ghi_chu` | Text | |

### `quan_he_doi_tuong` — Quan hệ giữa 2 đối tượng
| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `id` | Integer PK | |
| `cccd_1` | String FK → doi_tuong | CASCADE |
| `cccd_2` | String FK → doi_tuong | CASCADE |
| `loai_quan_he` | String | |
| `mo_ta` | Text | |
| `nguon_id` | Integer FK → nguon_du_lieu | |
| `do_tin_cay` | Integer | Default: 50. Thang 0–100 |
| `created_at` | DateTime | |

---

## Enum & Danh sách giá trị cố định (từ `backend/utils/constants.py`)

```python
GIOI_TINH_OPTIONS = ["Nam", "Nữ"]
TINH_OPTIONS = ["Phú Thọ", "Khác"]
PHAN_LOAI_NGHE_NGHIEP = [
    "Cơ quan nhà nước", "Tự kinh doanh", "Doanh nghiệp tư nhân",
    "Nông nghiệp", "Doanh nghiệp FDI", "Tổ chức phi chính phủ",
    "Học sinh/Sinh viên", "Về hưu", "Thất nghiệp", "Khác"
]
LOAI_LIEN_HE = ["SĐT", "Email", "Facebook", "Zalo", "Telegram", "Instagram", "Tiktok", "Khác"]
LOAI_XE = ["Ô tô", "Xe máy", "Xe tải", "Xe điện", "Xe đạp", "Thuyền/Ca nô", "Khác"]
LOAI_HINH_DAC_THU = {
    "Hon_Nhan_NN":         "Kết hôn với người nước ngoài",
    "Lam_Viec_NN":         "Làm việc cho tổ chức nước ngoài",
    "Hoc_Tap_Cong_Tac_NN": "Học tập/công tác nước ngoài",
    "Vi_Pham_NN":          "Vi phạm pháp luật nước ngoài",
    "Xac_Minh":            "Đã xác minh",
}
```

## Cột bắt buộc khi Import Excel (route `/nhap-excel/upload`)

| Cột Excel | Map sang | Ghi chú |
|-----------|----------|---------|
| `cccd` | `DoiTuong.cccd` | **Bắt buộc**. 9 hoặc 12 chữ số |
| `ho_ten` | `DoiTuong.ho_ten` | **Bắt buộc** |
| `ngay_sinh` | `DoiTuong.ngay_sinh` | Optional. Pandas có thể parse datetime hoặc string |
| `gioi_tinh` | `DoiTuong.gioi_tinh` | Optional. Phải là "Nam" hoặc "Nữ" |
| `dia_chi_tinh` | `DoiTuong.dia_chi_tinh` | Optional |
| `dia_chi_xa` | `DoiTuong.dia_chi_xa` | Optional |
| `phan_loai_nghe_nghiep` | `DoiTuong.phan_loai_nghe_nghiep` | Optional |
| `chi_tiet_nghe_nghiep` | `DoiTuong.chi_tiet_nghe_nghiep` | Optional |
| `ghi_chu_chung` | `DoiTuong.ghi_chu_chung` | Optional |
