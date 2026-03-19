# -*- coding: utf-8 -*-
"""
Database module cho hệ thống Security Profile 360
Tạo cơ sở dữ liệu SQLite với các bảng theo Schema PRD
"""

import atexit
import logging
import re
import sqlite3
import os
from contextlib import closing
import streamlit as st

# Tên file database
DB_NAME = "security_profile.db"

# Logging configuration
logger = logging.getLogger(__name__)


def get_db_path():
    """Lấy đường dẫn đầy đủ đến file database"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_NAME)


def get_connection():
    """Tạo kết nối đến database (SQLCipher encrypted)"""
    conn = sqlite3.connect(get_db_path())
    conn.execute(f"PRAGMA key='{st.secrets['DB_PASSWORD']}';")
    conn.row_factory = sqlite3.Row  # Cho phép truy cập cột theo tên
    # Bật foreign key constraints và cấu hình WAL cho SQLite
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


@st.cache_resource
def get_cached_connection():
    """Tạo connection dùng lại (cached), dùng cho read-only queries (SQLCipher encrypted)"""
    conn = sqlite3.connect(get_db_path(), check_same_thread=False)
    conn.execute(f"PRAGMA key='{st.secrets['DB_PASSWORD']}';")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def create_tables():
    """Tạo tất cả các bảng trong database"""
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
    
        # ========================================
        # BẢNG DỮ LIỆU GỐC (Trung tâm hệ thống)
        # ========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS doi_tuong (
                cccd TEXT PRIMARY KEY,
                ho_ten TEXT,
                ngay_sinh DATE,
                gioi_tinh TEXT,
                dia_chi_tinh TEXT DEFAULT 'Phú Thọ',
                dia_chi_xa TEXT,
                dia_chi_chi_tiet TEXT DEFAULT '',
                anh_chan_dung TEXT,
                phan_loai_nghe_nghiep TEXT,
                chi_tiet_nghe_nghiep TEXT,
                ghi_chu_chung TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
        # ========================================
        # BẢNG VỆ TINH - TẦNG 1
        # ========================================
    
        # Bảng liên hệ (SĐT, Email, Facebook, Zalo, Telegram)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lien_he (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cccd TEXT NOT NULL,
                loai_lien_he TEXT,
                gia_tri TEXT,
                ghi_chu TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cccd) REFERENCES doi_tuong(cccd) ON DELETE CASCADE
            )
        """)
    
        # Bảng tài chính (Tài khoản ngân hàng)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tai_chinh (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cccd TEXT NOT NULL,
                ngan_hang TEXT,
                so_tai_khoan TEXT,
                chu_tai_khoan TEXT,
                ghi_chu TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cccd) REFERENCES doi_tuong(cccd) ON DELETE CASCADE
            )
        """)
    
        # Bảng phương tiện (Xe cộ)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS phuong_tien (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cccd TEXT NOT NULL,
                loai_xe TEXT,
                bien_kiem_soat TEXT,
                ten_phuong_tien TEXT,
                ghi_chu TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cccd) REFERENCES doi_tuong(cccd) ON DELETE CASCADE
            )
        """)
    
        # Bảng nhân thân (Bố, Mẹ, Vợ/Chồng, Quan hệ khác)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nhan_than (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cccd TEXT NOT NULL,
                loai_quan_he TEXT NOT NULL,
                ho_ten TEXT,
                cccd_nhan_than TEXT,
                ngay_sinh DATE,
                gioi_tinh TEXT DEFAULT '',
                dia_chi_tinh TEXT DEFAULT '',
                dia_chi_xa TEXT DEFAULT '',
                nghe_nghiep TEXT,
                noi_o TEXT,
                ghi_chu TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cccd) REFERENCES doi_tuong(cccd) ON DELETE CASCADE
            )
        """)
    
        # Migration: thêm cột mới cho bảng nhan_than (bỏ qua nếu đã tồn tại)
        for col in ['gioi_tinh', 'dia_chi_tinh', 'dia_chi_xa', 'dia_chi_chi_tiet']:
            # SECURITY: Validate column name (whitelist approach)
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col):
                continue
            try:
                cursor.execute(f"ALTER TABLE nhan_than ADD COLUMN {col} TEXT DEFAULT ''")
            except Exception:
                pass  # Cột đã tồn tại
    
        # Migration: thêm phân đoạn địa chỉ chi tiết cho bảng doi_tuong
        try:
            cursor.execute("ALTER TABLE doi_tuong ADD COLUMN dia_chi_chi_tiet TEXT DEFAULT ''")
        except Exception:
            pass
    
        # ========================================
        # BẢNG ĐẶC THÙ - TẦNG 2 (Yếu tố nước ngoài & Nghiệp vụ)
        # ========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ho_so_dac_thu (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cccd TEXT NOT NULL,
                loai_hinh TEXT NOT NULL,
                noi_dung_chi_tiet TEXT,
                ghi_chu TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cccd) REFERENCES doi_tuong(cccd) ON DELETE CASCADE
            )
        """)
    
        # ========================================
        # BẢNG TÀI LIỆU ĐÍNH KÈM
        # ========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tai_lieu (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cccd TEXT NOT NULL,
                ten_file_goc TEXT,
                ten_file_luu TEXT,
                duong_dan TEXT,
                loai_tai_lieu TEXT,
                mo_ta TEXT,
                dung_luong INTEGER,
                dinh_dang TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cccd) REFERENCES doi_tuong(cccd) ON DELETE CASCADE
            )
        """)
    
        # ========================================
        # BẢNG QUÁ TRÌNH HOẠT ĐỘNG
        # ========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qua_trinh_hoat_dong (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cccd TEXT NOT NULL,
                thoi_gian TEXT,
                noi_dung TEXT,
                ghi_chu TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cccd) REFERENCES doi_tuong(cccd) ON DELETE CASCADE
            )
        """)
    
        # ========================================
        # BẢNG NGUỒN DỮ LIỆU (Source Tracking - OSINT Pattern)
        # ========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nguon_du_lieu (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ten_nguon TEXT NOT NULL,
                loai_nguon TEXT,
                thoi_gian_import TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                nguoi_import TEXT,
                file_goc TEXT,
                ghi_chu TEXT
            )
        """)
    
        # ========================================
        # BẢNG QUAN HỆ ĐỐI TƯỢNG (Person-to-Person Connection)
        # ========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quan_he_doi_tuong (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cccd_1 TEXT NOT NULL,
                cccd_2 TEXT NOT NULL,
                loai_quan_he TEXT,
                mo_ta TEXT,
                nguon_id INTEGER,
                do_tin_cay INTEGER DEFAULT 50,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cccd_1) REFERENCES doi_tuong(cccd) ON DELETE CASCADE,
                FOREIGN KEY (cccd_2) REFERENCES doi_tuong(cccd) ON DELETE CASCADE,
                FOREIGN KEY (nguon_id) REFERENCES nguon_du_lieu(id)
            )
        """)
    
        # ========================================
        # BẢNG LỊCH SỬ THAY ĐỔI (Audit Trail)
        # ========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bang TEXT NOT NULL,
                hanh_dong TEXT NOT NULL,
                khoa_chinh TEXT,
                du_lieu_cu TEXT,
                du_lieu_moi TEXT,
                nguoi_thuc_hien TEXT,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
        # ========================================
        # BẢNG NGƯỜI DÙNG (Authentication)
        # ========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                ho_ten TEXT,
                role TEXT DEFAULT 'user',
                is_active INTEGER DEFAULT 1,
                must_change_password INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)
    
        # Tạo index để tăng tốc truy vấn
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_lien_he_cccd ON lien_he(cccd)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tai_chinh_cccd ON tai_chinh(cccd)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_phuong_tien_cccd ON phuong_tien(cccd)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_nhan_than_cccd ON nhan_than(cccd)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_ho_so_dac_thu_cccd ON ho_so_dac_thu(cccd)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_ho_so_dac_thu_loai_hinh ON ho_so_dac_thu(loai_hinh)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_qua_trinh_hoat_dong_cccd ON qua_trinh_hoat_dong(cccd)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tai_lieu_cccd ON tai_lieu(cccd)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_doi_tuong_ho_ten ON doi_tuong(ho_ten)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_doi_tuong_created_at ON doi_tuong(created_at)")
    
        # Index cho tìm kiếm toàn diện (Multi-table Search)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_lien_he_gia_tri ON lien_he(gia_tri)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tai_chinh_so_tk ON tai_chinh(so_tai_khoan)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_phuong_tien_bien_ks ON phuong_tien(bien_kiem_soat)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_nhan_than_ho_ten ON nhan_than(ho_ten)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_nhan_than_cccd_nt ON nhan_than(cccd_nhan_than)")
    
        # Index cho các bảng mới
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_quan_he_cccd1 ON quan_he_doi_tuong(cccd_1)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_quan_he_cccd2 ON quan_he_doi_tuong(cccd_2)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_bang ON audit_log(bang)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_khoa ON audit_log(khoa_chinh)")
    
        conn.commit()


    print(f"[OK] Da tao database thanh cong: {get_db_path()}")
    print("[i] Cac bang da tao:")
    print("   - doi_tuong (Bang du lieu goc)")
    print("   - lien_he (Thong tin lien he)")
    print("   - tai_chinh (Tai khoan ngan hang)")
    print("   - phuong_tien (Phuong tien)")
    print("   - ho_so_dac_thu (Yeu to nuoc ngoai & Nghiep vu)")
    print("   - qua_trinh_hoat_dong (Qua trinh hoat dong)")
    print("   - nguon_du_lieu (Theo doi nguon du lieu)")
    print("   - quan_he_doi_tuong (Quan he giua cac doi tuong)")
    print("   - audit_log (Lich su thay doi)")


def save_qua_trinh_hoat_dong(cccd, thoi_gian, noi_dung, ghi_chu=""):
    """Lưu thông tin quá trình hoạt động"""
    if not noi_dung:
        return
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO qua_trinh_hoat_dong (cccd, thoi_gian, noi_dung, ghi_chu)
            VALUES (?, ?, ?, ?)
        """, (cccd, thoi_gian, noi_dung, ghi_chu))
        conn.commit()


def get_qua_trinh_hoat_dong(cccd):
    """Lấy danh sách quá trình hoạt động theo CCCD"""
    with closing(get_connection()) as conn:
        query = "SELECT * FROM qua_trinh_hoat_dong WHERE cccd = ? ORDER BY id DESC"
        cursor = conn.cursor()
        cursor.execute(query, (cccd,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def delete_qua_trinh_hoat_dong(qt_id: int) -> bool:
    """Xóa quá trình hoạt động theo ID"""
    try:
        with closing(get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM qua_trinh_hoat_dong WHERE id = ?", (qt_id,))
            conn.commit()
            return True
    except Exception:
        logger.error("Lỗi xóa quá trình hoạt động")
        return False


def verify_database():
    """Kiểm tra cấu trúc database đã tạo (chỉ đếm số bảng để tối ưu khởi động)"""
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        table_count = cursor.fetchone()[0]
        logger.info(f"Database đã sẵn sàng: {table_count} bảng.")


# ============================================
# BẢO VỆ FILE DATABASE - WAL CHECKPOINT KHI TẮT APP
# ============================================
def an_toan_dong_database():
    """Checkpoint WAL và dọn dẹp khi tiến trình Python/Streamlit tắt"""
    try:
        with closing(get_connection()) as conn:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        logging.info("[Bảo mật mức 1] Đã chốt sổ dữ liệu nháp (WAL) an toàn trước khi tắt hệ thống.")
    except Exception as e:
        logging.error("[Bảo mật mức 1] Lỗi khi dọn dẹp file WAL: " + str(e))


# Đăng ký hàm này chạy tự động mỗi khi tiến trình Python/Streamlit bị tắt
atexit.register(an_toan_dong_database)


if __name__ == "__main__":
    logger.info("Khởi tạo Database Security Profile 360...")
    create_tables()
    verify_database()
    logger.info("Hoàn tất! Database đã sẵn sàng sử dụng.")
