# -*- coding: utf-8 -*-
import logging
import shutil
from pathlib import Path
from database import get_connection

logger = logging.getLogger(__name__)

def delete_nhan_than(nhan_than_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM nhan_than WHERE id = ?", (nhan_than_id,))
    conn.commit()
    conn.close()
    return True


def delete_lien_he(lien_he_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM lien_he WHERE id = ?", (lien_he_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.exception(f"Lỗi xóa liên hệ: {e}")
        return False
    finally:
        conn.close()


def delete_tai_chinh(tai_chinh_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tai_chinh WHERE id = ?", (tai_chinh_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.exception(f"Lỗi xóa tài chính: {e}")
        return False
    finally:
        conn.close()


def delete_phuong_tien(phuong_tien_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM phuong_tien WHERE id = ?",
                       (phuong_tien_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.exception(f"Lỗi xóa phương tiện: {e}")
        return False
    finally:
        conn.close()


def delete_ho_so_dac_thu(ho_so_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ho_so_dac_thu WHERE id = ?", (ho_so_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.exception(f"Lỗi xóa hồ sơ đặc thù: {e}")
        return False
    finally:
        conn.close()


def delete_tai_lieu(tai_lieu_id):
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
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM doi_tuong WHERE cccd = ?", (cccd,))
        conn.commit()

        upload_folder = Path.cwd() / "uploads" / cccd
        if upload_folder.exists():
            shutil.rmtree(upload_folder)

        return True, "Đã xóa thành công!"
    except Exception as e:
        logger.exception(f"Lỗi xóa đối tượng: {e}")
        return False, "Đã xảy ra lỗi hệ thống. Vui lòng thử lại."
    finally:
        conn.close()


def update_doi_tuong(cccd, data):
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
    except Exception as e:
        logger.exception(f"Lỗi cập nhật đối tượng: {e}")
        return False, "Đã xảy ra lỗi hệ thống. Vui lòng thử lại."
    finally:
        conn.close()
