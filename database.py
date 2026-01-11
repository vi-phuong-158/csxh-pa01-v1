# -*- coding: utf-8 -*-
"""
Database module cho hệ thống Security Profile 360
Tạo cơ sở dữ liệu SQLite với các bảng theo Schema PRD
"""

import sqlite3
import os

# Tên file database
DB_NAME = "security_profile.db"


def get_db_path():
    """Lấy đường dẫn đầy đủ đến file database"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_NAME)


def get_connection():
    """Tạo kết nối đến database"""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row  # Cho phép truy cập cột theo tên
    # Bật foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_tables():
    """Tạo tất cả các bảng trong database"""
    conn = get_connection()
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
            nghe_nghiep TEXT,
            noi_o TEXT,
            ghi_chu TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cccd) REFERENCES doi_tuong(cccd) ON DELETE CASCADE
        )
    """)

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

    # Tạo index để tăng tốc truy vấn
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lien_he_cccd ON lien_he(cccd)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tai_chinh_cccd ON tai_chinh(cccd)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_phuong_tien_cccd ON phuong_tien(cccd)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_nhan_than_cccd ON nhan_than(cccd)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ho_so_dac_thu_cccd ON ho_so_dac_thu(cccd)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ho_so_dac_thu_loai_hinh ON ho_so_dac_thu(loai_hinh)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_qua_trinh_hoat_dong_cccd ON qua_trinh_hoat_dong(cccd)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tai_lieu_cccd ON tai_lieu(cccd)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_doi_tuong_ho_ten ON doi_tuong(ho_ten)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_doi_tuong_created_at ON doi_tuong(created_at)")

    conn.commit()
    conn.close()
    
    print(f"[OK] Da tao database thanh cong: {get_db_path()}")
    print("[i] Cac bang da tao:")
    print("   - doi_tuong (Bang du lieu goc)")
    print("   - lien_he (Thong tin lien he)")
    print("   - tai_chinh (Tai khoan ngan hang)")
    print("   - phuong_tien (Phuong tien)")
    print("   - ho_so_dac_thu (Yeu to nuoc ngoai & Nghiep vu)")
    print("   - qua_trinh_hoat_dong (Qua trinh hoat dong)")

def save_qua_trinh_hoat_dong(cccd, thoi_gian, noi_dung, ghi_chu=""):
    """Lưu thông tin quá trình hoạt động"""
    if not noi_dung:
        return
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO qua_trinh_hoat_dong (cccd, thoi_gian, noi_dung, ghi_chu)
            VALUES (?, ?, ?, ?)
        """, (cccd, thoi_gian, noi_dung, ghi_chu))
        conn.commit()
    finally:
        conn.close()

def get_qua_trinh_hoat_dong(cccd):
    """Lấy danh sách quá trình hoạt động theo CCCD"""
    conn = get_connection()
    try:
        # Sắp xếp theo ID giảm dần (mới nhất lên đầu) hoặc có thể parse thời gian nếu cần
        # Ở đây để đơn giản ta sort theo created_at/id
        query = "SELECT * FROM qua_trinh_hoat_dong WHERE cccd = ? ORDER BY id DESC"
        # Trả về list of sqlite3.Row -> có thể convert sang dict hoặc DataFrame
        # Để nhất quán với usage trong views (pandas read_sql), ta có thể dùng pandas ở view
        # Tuy nhiên user yêu cầu hàm này SELECT dữ liệu.
        # Ở đay trả về list dict cho linh hoạt
        cursor = conn.cursor()
        cursor.execute(query, (cccd,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

def delete_qua_trinh_hoat_dong(qt_id: int) -> bool:
    """Xóa quá trình hoạt động theo ID"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM qua_trinh_hoat_dong WHERE id = ?", (qt_id,))
        conn.commit()
        return True
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Lỗi xóa quá trình hoạt động: {e}")
        return False
    finally:
        conn.close()

import logging
import re

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def verify_database():
    """Kiểm tra cấu trúc database đã tạo"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # Lấy danh sách các bảng
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        logger.info("Cấu trúc Database:")
        
        for table in tables:
            table_name = table[0]
            if table_name.startswith("sqlite_"):
                continue
            
            # SECURITY: Sanitize table_name để tránh SQL injection
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
                logger.warning(f"Invalid table name detected: {table_name}")
                continue
                
            logger.info(f"[TABLE] {table_name}")
            
            # Lấy thông tin các cột - sau khi đã validate table_name
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            for col in columns:
                col_id, col_name, col_type, not_null, default_val, is_pk = col
                pk_marker = "[PK]" if is_pk else "    "
                null_marker = "NOT NULL" if not_null else ""
                default_marker = f"DEFAULT {default_val}" if default_val else ""
                logger.debug(f"   {pk_marker} {col_name}: {col_type} {null_marker} {default_marker}")
    finally:
        conn.close()


if __name__ == "__main__":
    logger.info("Khởi tạo Database Security Profile 360...")
    create_tables()
    verify_database()
    logger.info("Hoàn tất! Database đã sẵn sàng sử dụng.")

