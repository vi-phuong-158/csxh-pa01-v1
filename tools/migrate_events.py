"""
migrate_events.py — Thêm cột ngay_bat_dau & ngay_ket_thuc vào bảng qua_trinh_hoat_dong
Sử dụng SQLAlchemy (hỗ trợ SQLCipher nếu được cấu hình trong .env).
Chạy 1 lần: python tools/migrate_events.py
"""
import sys
from pathlib import Path

# Thêm project root vào sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from backend.db.session import SessionLocal

def run_migration():
    db = SessionLocal()
    try:
        # Kiểm tra cột hiện có
        result = db.execute(text("PRAGMA table_info(qua_trinh_hoat_dong)"))
        existing_cols = {row[1] for row in result.fetchall()}

        added = []

        if "ngay_bat_dau" not in existing_cols:
            db.execute(text("ALTER TABLE qua_trinh_hoat_dong ADD COLUMN ngay_bat_dau DATE"))
            added.append("ngay_bat_dau")

        if "ngay_ket_thuc" not in existing_cols:
            db.execute(text("ALTER TABLE qua_trinh_hoat_dong ADD COLUMN ngay_ket_thuc DATE"))
            added.append("ngay_ket_thuc")

        # Index tăng tốc truy vấn thông báo
        db.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_qthd_ngay_ket_thuc "
            "ON qua_trinh_hoat_dong(ngay_ket_thuc)"
        ))

        db.commit()

        if added:
            print(f"[OK] Đã thêm cột: {', '.join(added)}")
        else:
            print("[OK] Các cột đã tồn tại, không cần thay đổi.")

        print("[DONE] Migration hoàn tất.")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Migration thất bại: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_migration()
