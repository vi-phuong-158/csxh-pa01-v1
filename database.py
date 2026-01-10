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
    
    # Tạo index để tăng tốc truy vấn
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lien_he_cccd ON lien_he(cccd)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tai_chinh_cccd ON tai_chinh(cccd)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_phuong_tien_cccd ON phuong_tien(cccd)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_nhan_than_cccd ON nhan_than(cccd)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ho_so_dac_thu_cccd ON ho_so_dac_thu(cccd)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ho_so_dac_thu_loai_hinh ON ho_so_dac_thu(loai_hinh)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tai_lieu_cccd ON tai_lieu(cccd)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_doi_tuong_ho_ten ON doi_tuong(ho_ten)")

    conn.commit()
    conn.close()
    
    print(f"[OK] Da tao database thanh cong: {get_db_path()}")
    print("[i] Cac bang da tao:")
    print("   - doi_tuong (Bang du lieu goc)")
    print("   - lien_he (Thong tin lien he)")
    print("   - tai_chinh (Tai khoan ngan hang)")
    print("   - phuong_tien (Phuong tien)")
    print("   - ho_so_dac_thu (Yeu to nuoc ngoai & Nghiep vu)")


def verify_database():
    """Kiểm tra cấu trúc database đã tạo"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Lấy danh sách các bảng
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    print("\n[i] Cau truc Database:")
    print("=" * 50)
    
    for table in tables:
        table_name = table[0]
        if table_name.startswith("sqlite_"):
            continue
            
        print(f"\n[TABLE] {table_name}")
        
        # Lấy thông tin các cột
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        for col in columns:
            col_id, col_name, col_type, not_null, default_val, is_pk = col
            pk_marker = "[PK]" if is_pk else "    "
            null_marker = "NOT NULL" if not_null else ""
            default_marker = f"DEFAULT {default_val}" if default_val else ""
            line = f"   {pk_marker} {col_name}: {col_type} {null_marker} {default_marker}".strip()
            # Encode to ASCII to avoid Unicode errors on Windows console
            print(line.encode('ascii', 'replace').decode('ascii'))
    
    conn.close()


if __name__ == "__main__":
    print("[*] Khoi tao Database Security Profile 360...")
    print("=" * 50)
    create_tables()
    verify_database()
    print("\n" + "=" * 50)
    print("[OK] Hoan tat! Database da san sang su dung.")
