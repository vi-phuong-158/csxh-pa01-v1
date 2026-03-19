# -*- coding: utf-8 -*-
"""
Service Layer - Xử lý business logic
Tách từ nhap_lieu.py và ho_so_chi_tiet.py để tránh circular import

Module này chứa tất cả các hàm save/delete/update cho database.
Các views chỉ cần import từ đây thay vì import lẫn nhau.
"""

import json
import logging
import re
import uuid
from pathlib import Path
from datetime import datetime

from database import get_connection
from constants import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB

try:
    import magic  # type: ignore
except ImportError:  # Fallback nếu python-magic chưa được cài
    magic = None

logger = logging.getLogger(__name__)

# ============================================
# HELPER FUNCTIONS
# ============================================

def validate_cccd(cccd: str) -> bool:
    """
    Validate CCCD string to prevent path traversal and injection.
    Only allows alphanumeric characters.
    """
    if not cccd:
        return False
    # Only allow alphanumeric characters
    return cccd.isalnum()

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename để ngăn path traversal và injection attacks.

    Bảo vệ chống:
    - Path traversal (../)
    - Null byte injection
    - Ký tự đặc biệt nguy hiểm
    - Filename quá dài
    """
    import os

    if not filename:
        return 'unnamed_file'

    # Lấy tên file, loại bỏ path
    filename = Path(filename).name

    # Loại bỏ null bytes (null byte injection)
    filename = filename.replace('\x00', '')

    # Loại bỏ các ký tự đặc biệt nguy hiểm
    # Chỉ giữ lại: chữ cái (bao gồm Unicode), số, dấu gạch ngang, gạch dưới, dấu chấm, khoảng trắng
    filename = re.sub(r'[^\w\-_\. ]', '', filename, flags=re.UNICODE)

    # Loại bỏ path traversal patterns
    filename = filename.replace('..', '')

    # Giới hạn độ dài filename
    max_length = 200
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext

    return filename.strip() if filename.strip() else 'unnamed_file'


def get_upload_folder(cccd):
    """Lấy thư mục upload cho một CCCD"""
    if not validate_cccd(cccd):
        raise ValueError("Invalid CCCD: Must be alphanumeric only")

    base_path = Path(__file__).parent / "uploads" / cccd
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path


# ============================================
# SAVE FUNCTIONS
# ============================================

def save_lien_he(cccd, loai, gia_tri, ghi_chu=""):
    """Lưu thông tin liên hệ"""
    if not gia_tri:
        return False
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO lien_he (cccd, loai_lien_he, gia_tri, ghi_chu)
            VALUES (?, ?, ?, ?)
        """, (cccd, loai, gia_tri, ghi_chu))
        conn.commit()
        return True
    except Exception:
        logger.exception("Lỗi lưu liên hệ")
        return False
    finally:
        conn.close()


def save_tai_chinh(cccd, ngan_hang, so_tai_khoan, chu_tai_khoan="", ghi_chu=""):
    """Lưu thông tin tài khoản ngân hàng"""
    if not so_tai_khoan:
        return False
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tai_chinh (cccd, ngan_hang, so_tai_khoan, chu_tai_khoan, ghi_chu)
            VALUES (?, ?, ?, ?, ?)
        """, (cccd, ngan_hang, so_tai_khoan, chu_tai_khoan, ghi_chu))
        conn.commit()
        return True
    except Exception:
        logger.exception("Lỗi lưu tài chính")
        return False
    finally:
        conn.close()


def save_phuong_tien(cccd, loai_xe, bien_so, ten_xe, ghi_chu=""):
    """Lưu thông tin phương tiện"""
    if not bien_so:
        return False
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO phuong_tien (cccd, loai_xe, bien_kiem_soat, ten_phuong_tien, ghi_chu)
            VALUES (?, ?, ?, ?, ?)
        """, (cccd, loai_xe, bien_so, ten_xe, ghi_chu))
        conn.commit()
        return True
    except Exception:
        logger.exception("Lỗi lưu phương tiện")
        return False
    finally:
        conn.close()


def save_nhan_than(cccd, loai_quan_he, ho_ten, cccd_nhan_than="", ngay_sinh=None,
                   gioi_tinh="", dia_chi_tinh="", dia_chi_xa="", dia_chi_chi_tiet="",
                   nghe_nghiep="", noi_o="", ghi_chu=""):
    """Lưu thông tin nhân thân"""
    if not ho_ten:
        return False
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO nhan_than (cccd, loai_quan_he, ho_ten, cccd_nhan_than, ngay_sinh,
                                   gioi_tinh, dia_chi_tinh, dia_chi_xa, dia_chi_chi_tiet,
                                   nghe_nghiep, noi_o, ghi_chu)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (cccd, loai_quan_he, ho_ten, cccd_nhan_than, ngay_sinh,
              gioi_tinh, dia_chi_tinh, dia_chi_xa, dia_chi_chi_tiet,
              nghe_nghiep, noi_o, ghi_chu))
        conn.commit()
        return True
    except Exception:
        logger.exception("Lỗi lưu nhân thân")
        return False
    finally:
        conn.close()


def save_ho_so_dac_thu(cccd, loai_hinh, noi_dung_dict, ghi_chu=""):
    """Lưu hồ sơ đặc thù (CSXH)"""
    if not noi_dung_dict:
        return False
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ho_so_dac_thu (cccd, loai_hinh, noi_dung_chi_tiet, ghi_chu)
            VALUES (?, ?, ?, ?)
        """, (cccd, loai_hinh, json.dumps(noi_dung_dict, ensure_ascii=False), ghi_chu))
        conn.commit()
        return True
    except Exception:
        logger.exception("Lỗi lưu hồ sơ đặc thù")
        return False
    finally:
        conn.close()


def save_tai_lieu(cccd, uploaded_file, loai_tai_lieu, mo_ta=""):
    """Lưu tài liệu đính kèm"""
    if not uploaded_file:
        return False, "Không có file"

    file_bytes = uploaded_file.getvalue()
    file_size = len(file_bytes)
    if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        return False, f"File quá lớn! Giới hạn {MAX_FILE_SIZE_MB}MB"

    # Kiểm tra extension bề mặt
    file_ext = uploaded_file.name.split('.')[-1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return False, f"Định dạng không hỗ trợ! Chỉ chấp nhận: {', '.join(ALLOWED_EXTENSIONS)}"

    # Xác thực MIME type thực tế (ưu tiên python-magic)
    detected_mime = None
    if magic is not None:
        try:
            m = magic.Magic(mime=True)
            detected_mime = m.from_buffer(file_bytes[:2048])
        except Exception:
            logger.warning("Lỗi detect MIME bằng python-magic")
    else:
        # Fallback: kiểm tra vài header bytes cơ bản
        header = file_bytes[:4]
        if header.startswith(b"\xFF\xD8"):
            detected_mime = "image/jpeg"
        elif header.startswith(b"\x89PNG"):
            detected_mime = "image/png"
        elif header.startswith(b"%PDF"):
            detected_mime = "application/pdf"

    if detected_mime:
        # Ánh xạ ext -> mime hợp lệ
        allowed_mime_by_ext = {
            "jpg": ["image/jpeg"],
            "jpeg": ["image/jpeg"],
            "png": ["image/png"],
            "pdf": ["application/pdf"],
        }
        allowed_mimes = allowed_mime_by_ext.get(file_ext, [])
        if allowed_mimes and detected_mime not in allowed_mimes:
            logger.error(
                "Security: MIME type mismatch for upload. Extension và nội dung không khớp."
            )
            return False, "Định dạng file không khớp nội dung thực tế. Vui lòng kiểm tra lại."

    safe_filename = sanitize_filename(uploaded_file.name)
    unique_name = f"{uuid.uuid4().hex[:8]}_{safe_filename}"

    upload_folder = get_upload_folder(cccd)
    file_path = upload_folder / unique_name

    try:
        with open(file_path, "wb") as f:
            f.write(file_bytes)
    except Exception:
        logger.exception("Lỗi lưu file")
        return False, "Đã xảy ra lỗi khi lưu file. Vui lòng thử lại."

    duong_dan = f"uploads/{cccd}/{unique_name}"
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tai_lieu (cccd, ten_file_goc, ten_file_luu, duong_dan, loai_tai_lieu, mo_ta, dung_luong, dinh_dang)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (cccd, safe_filename, unique_name, duong_dan, loai_tai_lieu, mo_ta, file_size, file_ext))
        conn.commit()
        return True, "Đã upload thành công!"
    except Exception:
        logger.exception("Lỗi lưu metadata")
        if file_path.exists():
            file_path.unlink()
        return False, "Đã xảy ra lỗi hệ thống. Vui lòng thử lại."
    finally:
        conn.close()


def save_doi_tuong(data):
    """Lưu thông tin đối tượng chính"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO doi_tuong (cccd, ho_ten, ngay_sinh, gioi_tinh, dia_chi_tinh, 
                                   dia_chi_xa, dia_chi_chi_tiet, anh_chan_dung, phan_loai_nghe_nghiep, 
                                   chi_tiet_nghe_nghiep, ghi_chu_chung)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(cccd) DO UPDATE SET
                ho_ten = excluded.ho_ten,
                ngay_sinh = excluded.ngay_sinh,
                gioi_tinh = excluded.gioi_tinh,
                dia_chi_tinh = excluded.dia_chi_tinh,
                dia_chi_xa = excluded.dia_chi_xa,
                dia_chi_chi_tiet = excluded.dia_chi_chi_tiet,
                phan_loai_nghe_nghiep = excluded.phan_loai_nghe_nghiep,
                chi_tiet_nghe_nghiep = excluded.chi_tiet_nghe_nghiep,
                ghi_chu_chung = excluded.ghi_chu_chung,
                updated_at = CURRENT_TIMESTAMP
        """, (
            data['cccd'],
            data['ho_ten'],
            data['ngay_sinh'],
            data['gioi_tinh'],
            data['dia_chi_tinh'],
            data['dia_chi_xa'],
            data.get('dia_chi_chi_tiet', ''),
            data.get('anh_chan_dung', ''),
            data['phan_loai_nghe_nghiep'],
            data['chi_tiet_nghe_nghiep'],
            data['ghi_chu_chung']
        ))

        # Handle Avatar Upload AFTER inserting record
        avatar_file = data.get('avatar_file')
        if avatar_file:
            try:
                # SECURITY CHECK: Validate file extension
                parts = avatar_file.name.split('.')
                if len(parts) > 1:
                    file_ext = parts[-1].lower()
                else:
                    file_ext = ""

                if file_ext not in ALLOWED_EXTENSIONS:
                    logger.error("Security: Attempted to upload invalid extension for avatar")
                    conn.rollback()
                    return False, f"Định dạng ảnh không hợp lệ! Chỉ chấp nhận: {', '.join(ALLOWED_EXTENSIONS)}"

                # SECURITY: Validate CCCD before using in file path
                if not validate_cccd(data['cccd']):
                    logger.error("Security: Invalid CCCD for avatar path")
                    conn.rollback()
                    return False, "CCCD không hợp lệ"

                import time
                base_path = Path(__file__).parent / "uploads" / data['cccd']
                base_path.mkdir(parents=True, exist_ok=True)

                safe_name = f"avatar_{int(time.time())}.{file_ext}"
                save_path = base_path / safe_name

                with open(save_path, "wb") as f:
                    f.write(avatar_file.getbuffer())

                relative_path = f"uploads/{data['cccd']}/{safe_name}"
                cursor.execute("UPDATE doi_tuong SET anh_chan_dung = ? WHERE cccd = ?",
                               (relative_path, data['cccd']))
            except Exception:
                logger.error("Error saving avatar on create")

        conn.commit()
        return True, "Lưu thành công!"
    except Exception:
        logger.exception("Lỗi lưu đối tượng")
        return False, "Đã xảy ra lỗi hệ thống. Vui lòng thử lại."
    finally:
        conn.close()


# ============================================
# CHECK FUNCTIONS
# ============================================

def check_cccd_exists(cccd: str) -> bool:
    """Kiểm tra CCCD đã tồn tại chưa"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM doi_tuong WHERE cccd = ?", (cccd,))
        count = cursor.fetchone()[0]
        return count > 0
    finally:
        conn.close()
