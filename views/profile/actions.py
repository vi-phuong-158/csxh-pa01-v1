# -*- coding: utf-8 -*-
import logging
import shutil
from pathlib import Path
from database import get_connection

logger = logging.getLogger(__name__)


def _validate_id(value) -> bool:
    """Validate integer ID input"""
    return value is not None and str(value).isdigit()


def _validate_cccd(value) -> bool:
    """Validate CCCD input"""
    return value is not None and str(value).isalnum()

def delete_nhan_than(nhan_than_id):
    if not _validate_id(nhan_than_id):
        return False
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM nhan_than WHERE id = ?", (nhan_than_id,))
        conn.commit()
        return True
    except Exception:
        logger.exception("Lỗi xóa nhân thân (ID đã được kiểm tra)")
        return False
    finally:
        conn.close()


def delete_lien_he(lien_he_id: int) -> bool:
    if not _validate_id(lien_he_id):
        return False
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM lien_he WHERE id = ?", (lien_he_id,))
        conn.commit()
        return True
    except Exception:
        logger.exception("Lỗi xóa liên hệ")
        return False
    finally:
        conn.close()


def delete_tai_chinh(tai_chinh_id: int) -> bool:
    if not _validate_id(tai_chinh_id):
        return False
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tai_chinh WHERE id = ?", (tai_chinh_id,))
        conn.commit()
        return True
    except Exception:
        logger.exception("Lỗi xóa tài chính")
        return False
    finally:
        conn.close()


def delete_phuong_tien(phuong_tien_id: int) -> bool:
    if not _validate_id(phuong_tien_id):
        return False
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM phuong_tien WHERE id = ?",
                       (phuong_tien_id,))
        conn.commit()
        return True
    except Exception:
        logger.exception("Lỗi xóa phương tiện")
        return False
    finally:
        conn.close()


def delete_ho_so_dac_thu(ho_so_id: int) -> bool:
    if not _validate_id(ho_so_id):
        return False
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ho_so_dac_thu WHERE id = ?", (ho_so_id,))
        conn.commit()
        return True
    except Exception:
        logger.exception("Lỗi xóa hồ sơ đặc thù")
        return False
    finally:
        conn.close()


def delete_tai_lieu(tai_lieu_id):
    if not _validate_id(tai_lieu_id):
        return False
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT duong_dan FROM tai_lieu WHERE id = ?", (tai_lieu_id,))
    result = cursor.fetchone()

    if result:
        duong_dan = result[0]
        file_path = Path.cwd() / duong_dan
        if file_path.exists():
            file_path.unlink()

        cursor.execute("DELETE FROM tai_lieu WHERE id = ?", (tai_lieu_id,))
        conn.commit()

    conn.close()
    return True


def delete_doi_tuong(cccd):
    if not _validate_cccd(cccd):
        return False, "CCCD không hợp lệ"
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM doi_tuong WHERE cccd = ?", (cccd,))
        conn.commit()

        upload_folder = Path.cwd() / "uploads" / cccd
        if upload_folder.exists():
            shutil.rmtree(upload_folder)

        return True, "Đã xóa thành công!"
    except Exception:
        logger.exception("Lỗi xóa đối tượng")
        return False, "Đã xảy ra lỗi hệ thống. Vui lòng thử lại."
    finally:
        conn.close()


def update_doi_tuong(cccd, data):
    if not _validate_cccd(cccd):
        return False, "CCCD không hợp lệ"
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE doi_tuong 
            SET ho_ten = ?, ngay_sinh = ?, gioi_tinh = ?, dia_chi_tinh = ?,
                dia_chi_xa = ?, dia_chi_chi_tiet = ?, phan_loai_nghe_nghiep = ?, chi_tiet_nghe_nghiep = ?,
                ghi_chu_chung = ?, anh_chan_dung = ?, updated_at = CURRENT_TIMESTAMP
            WHERE cccd = ?
        """, (
            data['ho_ten'],
            data['ngay_sinh'],
            data['gioi_tinh'],
            data['dia_chi_tinh'],
            data['dia_chi_xa'],
            data.get('dia_chi_chi_tiet', ''),
            data['phan_loai_nghe_nghiep'],
            data['chi_tiet_nghe_nghiep'],
            data['ghi_chu_chung'],
            data.get('anh_chan_dung'),
            cccd
        ))
        conn.commit()
        return True, "Cập nhật thành công!"
    except Exception:
        logger.exception("Lỗi cập nhật đối tượng")
        return False, "Đã xảy ra lỗi hệ thống. Vui lòng thử lại."
    finally:
        conn.close()
