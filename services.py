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

logger = logging.getLogger(__name__)

# ============================================
# HELPER FUNCTIONS
# ============================================

def validate_cccd(cccd: str) -> bool:
    """
    Validate CCCD format (must be 12 digits).
    Raises ValueError if invalid to prevent injection/traversal.
    """
    if not cccd:
        raise ValueError("CCCD cannot be empty")

    if not isinstance(cccd, str):
        cccd = str(cccd)

    if len(cccd) != 12 or not cccd.isdigit():
        raise ValueError("CCCD must be exactly 12 digits")

    return True


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
    validate_cccd(cccd)
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
    except Exception as e:
        logger.exception(f"Lỗi lưu liên hệ: {e}")
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
    except Exception as e:
        logger.exception(f"Lỗi lưu tài chính: {e}")
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
    except Exception as e:
        logger.exception(f"Lỗi lưu phương tiện: {e}")
        return False
    finally:
        conn.close()


def save_nhan_than(cccd, loai_quan_he, ho_ten, cccd_nhan_than="", ngay_sinh=None, nghe_nghiep="", noi_o="", ghi_chu=""):
    """Lưu thông tin nhân thân"""
    if not ho_ten:
        return False
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO nhan_than (cccd, loai_quan_he, ho_ten, cccd_nhan_than, ngay_sinh, nghe_nghiep, noi_o, ghi_chu)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (cccd, loai_quan_he, ho_ten, cccd_nhan_than, ngay_sinh, nghe_nghiep, noi_o, ghi_chu))
        conn.commit()
        return True
    except Exception as e:
        logger.exception(f"Lỗi lưu nhân thân: {e}")
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
    except Exception as e:
        logger.exception(f"Lỗi lưu hồ sơ đặc thù: {e}")
        return False
    finally:
        conn.close()


def save_tai_lieu(cccd, uploaded_file, loai_tai_lieu, mo_ta=""):
    """Lưu tài liệu đính kèm"""
    if not uploaded_file:
        return False, "Không có file"
    
    file_size = len(uploaded_file.getvalue())
    if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        return False, f"File quá lớn! Giới hạn {MAX_FILE_SIZE_MB}MB"
    
    file_ext = uploaded_file.name.split('.')[-1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return False, f"Định dạng không hỗ trợ! Chỉ chấp nhận: {', '.join(ALLOWED_EXTENSIONS)}"
    
    safe_filename = sanitize_filename(uploaded_file.name)
    unique_name = f"{uuid.uuid4().hex[:8]}_{safe_filename}"
    
    upload_folder = get_upload_folder(cccd)
    file_path = upload_folder / unique_name
    
    try:
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getvalue())
    except Exception as e:
        logger.exception(f"Lỗi lưu file: {e}")
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
    except Exception as e:
        logger.exception(f"Lỗi lưu metadata: {e}")
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
                                   dia_chi_xa, anh_chan_dung, phan_loai_nghe_nghiep, 
                                   chi_tiet_nghe_nghiep, ghi_chu_chung)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['cccd'],
            data['ho_ten'],
            data['ngay_sinh'],
            data['gioi_tinh'],
            data['dia_chi_tinh'],
            data['dia_chi_xa'],
            data.get('anh_chan_dung', ''),
            data['phan_loai_nghe_nghiep'],
            data['chi_tiet_nghe_nghiep'],
            data['ghi_chu_chung']
        ))
        
        # Handle Avatar Upload AFTER inserting record
        avatar_file = data.get('avatar_file')
        if avatar_file:
            try:
                import time
                # Use secured function
                base_path = get_upload_folder(data['cccd'])
                
                file_ext = avatar_file.name.split('.')[-1]
                safe_name = f"avatar_{int(time.time())}.{file_ext}"
                save_path = base_path / safe_name
                
                with open(save_path, "wb") as f:
                    f.write(avatar_file.getbuffer())
                
                relative_path = f"uploads/{data['cccd']}/{safe_name}"
                cursor.execute("UPDATE doi_tuong SET anh_chan_dung = ? WHERE cccd = ?", 
                             (relative_path, data['cccd']))
            except Exception as e:
                logger.error(f"Error saving avatar on create: {e}")
        
        conn.commit()
        return True, "Lưu thành công!"
    except Exception as e:
        logger.exception(f"Lỗi lưu đối tượng: {e}")
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
        cursor.execute("SELECT COUNT(*) FROM doi_tuong WHERE cccd = ?", (cccd,))
        count = cursor.fetchone()[0]
        return count > 0
    finally:
        conn.close()
