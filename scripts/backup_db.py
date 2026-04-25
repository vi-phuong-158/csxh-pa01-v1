# -*- coding: utf-8 -*-
"""
Backup Script - VCFE Database
=====================================
Tự động sao lưu cơ sở dữ liệu `security_profile.db` hàng ngày.

Tính năng:
- Sao lưu database vào thư mục `backups/` (cùng cấp với script)
- Nén thành file `.zip` để tiết kiệm dung lượng
- Giữ lại tối đa 7 bản backup gần nhất (tự động xóa bản cũ)
- Kiểm tra tính toàn vẹn database trước khi backup
- Ghi log mọi hoạt động backup

Cách sử dụng:
    # Chạy thủ công:
    python scripts/backup_db.py

    # Cài đặt Windows Task Scheduler (chạy hàng ngày lúc 02:00):
    python scripts/backup_db.py --install-task

    # Tùy chỉnh số ngày giữ lại:
    python scripts/backup_db.py --keep-days 14

    # Chỉ định đường dẫn database khác:
    python scripts/backup_db.py --db-path "C:/path/to/security_profile.db"
"""

import argparse
import logging
import os
import shutil
import sqlite3
import subprocess
import sys
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

# ============================================
# CẤU HÌNH MẶC ĐỊNH
# ============================================
DEFAULT_KEEP_DAYS = 7           # Giữ lại 7 ngày gần nhất
DEFAULT_DB_NAME = "security_profile.db"
BACKUP_DIR_NAME = "backups"
LOG_FILE_NAME = "backup.log"
TASK_NAME = "SecurityProfile360_DailyBackup"

# ============================================
# THIẾT LẬP LOGGING
# ============================================

# Thư mục gốc dự án (parent của scripts/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKUP_DIR = PROJECT_ROOT / BACKUP_DIR_NAME
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# Cấu hình logger
logger = logging.getLogger("backup")
logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(
    logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
)
logger.addHandler(console_handler)

# File handler
log_file = BACKUP_DIR / LOG_FILE_NAME
file_handler = logging.FileHandler(log_file, encoding="utf-8")
file_handler.setFormatter(
    logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
)
logger.addHandler(file_handler)


# ============================================
# HÀM CHỨC NĂNG
# ============================================

def get_db_path(custom_path: str | None = None) -> Path:
    """Xác định đường dẫn đến file database."""
    if custom_path:
        db_path = Path(custom_path)
    else:
        db_path = PROJECT_ROOT / DEFAULT_DB_NAME

    if not db_path.exists():
        logger.error(f"Không tìm thấy database: {db_path}")
        sys.exit(1)

    return db_path


def check_db_integrity(db_path: Path) -> bool:
    """
    Kiểm tra tính toàn vẹn của database trước khi backup.
    Sử dụng PRAGMA integrity_check của SQLite.
    """
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        conn.close()

        if result and result[0] == "ok":
            logger.info("✅ Database integrity check: OK")
            return True
        else:
            logger.warning(f"⚠️ Database integrity check failed: {result}")
            return False
    except Exception as e:
        logger.error(f"❌ Lỗi kiểm tra integrity: {e}")
        return False


def get_db_stats(db_path: Path) -> dict:
    """Lấy thống kê cơ bản của database."""
    stats = {
        "file_size_mb": db_path.stat().st_size / (1024 * 1024),
        "tables": [],
        "total_records": 0,
    }
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]

        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
            count = cursor.fetchone()[0]
            stats["tables"].append({"name": table, "records": count})
            stats["total_records"] += count

        conn.close()
    except Exception as e:
        logger.warning(f"Không thể lấy thống kê DB: {e}")

    return stats


def create_backup(db_path: Path) -> Path | None:
    """
    Tạo bản backup nén ZIP của database.
    
    Returns:
        Path tới file backup ZIP nếu thành công, None nếu thất bại.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"security_profile_backup_{timestamp}"
    backup_db_file = BACKUP_DIR / f"{backup_name}.db"
    backup_zip_file = BACKUP_DIR / f"{backup_name}.zip"

    try:
        # Bước 1: Copy database file (dùng SQLite backup API cho an toàn)
        logger.info(f"📦 Đang sao lưu database...")

        source_conn = sqlite3.connect(str(db_path))
        backup_conn = sqlite3.connect(str(backup_db_file))

        # Sử dụng SQLite Online Backup API - an toàn với WAL mode
        source_conn.backup(backup_conn)

        backup_conn.close()
        source_conn.close()

        logger.info(f"   Đã copy database: {backup_db_file.name}")

        # Bước 2: Nén thành ZIP
        with zipfile.ZipFile(backup_zip_file, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            zf.write(backup_db_file, f"{backup_name}.db")

        # Bước 3: Xóa file .db tạm (chỉ giữ ZIP)
        backup_db_file.unlink()

        # Thống kê
        original_size = db_path.stat().st_size
        zip_size = backup_zip_file.stat().st_size
        compression_ratio = (1 - zip_size / original_size) * 100 if original_size > 0 else 0

        logger.info(f"   📁 File backup: {backup_zip_file.name}")
        logger.info(f"   📊 Kích thước gốc: {original_size / 1024:.1f} KB")
        logger.info(f"   📊 Kích thước nén: {zip_size / 1024:.1f} KB")
        logger.info(f"   📊 Tỷ lệ nén: {compression_ratio:.1f}%")

        return backup_zip_file

    except Exception as e:
        logger.error(f"❌ Lỗi tạo backup: {e}")
        # Cleanup nếu có file dở dang
        if backup_db_file.exists():
            backup_db_file.unlink()
        if backup_zip_file.exists():
            backup_zip_file.unlink()
        return None


def cleanup_old_backups(keep_days: int = DEFAULT_KEEP_DAYS) -> int:
    """
    Xóa các bản backup cũ hơn `keep_days` ngày.
    
    Returns:
        Số file đã xóa.
    """
    cutoff_date = datetime.now() - timedelta(days=keep_days)
    deleted_count = 0

    for backup_file in BACKUP_DIR.glob("security_profile_backup_*.zip"):
        file_mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
        if file_mtime < cutoff_date:
            try:
                backup_file.unlink()
                logger.info(f"   🗑️ Đã xóa backup cũ: {backup_file.name} ({file_mtime.strftime('%Y-%m-%d')})")
                deleted_count += 1
            except Exception as e:
                logger.warning(f"   ⚠️ Không thể xóa {backup_file.name}: {e}")

    return deleted_count


def list_existing_backups() -> list[dict]:
    """Liệt kê tất cả các bản backup hiện có."""
    backups = []
    for backup_file in sorted(BACKUP_DIR.glob("security_profile_backup_*.zip"), reverse=True):
        stat = backup_file.stat()
        backups.append({
            "name": backup_file.name,
            "size_kb": stat.st_size / 1024,
            "created": datetime.fromtimestamp(stat.st_mtime),
        })
    return backups


def install_windows_task():
    """
    Cài đặt Windows Task Scheduler để chạy backup tự động hàng ngày lúc 02:00.
    Yêu cầu quyền Administrator.
    """
    if sys.platform != "win32":
        logger.error("Chức năng này chỉ hỗ trợ Windows!")
        return False

    python_exe = sys.executable
    script_path = Path(__file__).resolve()

    # Tạo lệnh schtasks
    cmd = [
        "schtasks", "/create",
        "/tn", TASK_NAME,
        "/tr", f'"{python_exe}" "{script_path}"',
        "/sc", "daily",
        "/st", "02:00",
        "/f",  # Force overwrite nếu đã tồn tại
        "/rl", "HIGHEST",  # Run with highest privileges
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"✅ Đã cài đặt Task Scheduler: {TASK_NAME}")
        logger.info(f"   Lịch: Hàng ngày lúc 02:00")
        logger.info(f"   Script: {script_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Lỗi cài đặt Task Scheduler: {e.stderr}")
        logger.info("💡 Hãy chạy lại với quyền Administrator!")
        return False
    except FileNotFoundError:
        logger.error("❌ Không tìm thấy schtasks.exe. Đảm bảo đang chạy trên Windows.")
        return False


# ============================================
# HÀM CHÍNH
# ============================================

def run_backup(db_path_str: str | None = None, keep_days: int = DEFAULT_KEEP_DAYS):
    """
    Thực hiện quy trình backup đầy đủ:
    1. Kiểm tra database tồn tại
    2. Kiểm tra tính toàn vẹn
    3. Tạo backup (nén ZIP)
    4. Dọn dẹp backup cũ
    5. Hiển thị danh sách backup
    """
    logger.info("=" * 60)
    logger.info("🔄 BẮT ĐẦU SAO LƯU DATABASE")
    logger.info(f"   Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # 1. Xác định và kiểm tra database
    db_path = get_db_path(db_path_str)
    logger.info(f"📂 Database: {db_path}")

    # 2. Thống kê database
    stats = get_db_stats(db_path)
    logger.info(f"📊 Kích thước: {stats['file_size_mb']:.2f} MB")
    logger.info(f"📊 Tổng bản ghi: {stats['total_records']}")

    # 3. Kiểm tra integrity
    if not check_db_integrity(db_path):
        logger.warning("⚠️ Database có thể bị hỏng! Vẫn tiếp tục backup...")

    # 4. Tạo backup
    backup_file = create_backup(db_path)
    if not backup_file:
        logger.error("❌ BACKUP THẤT BẠI!")
        sys.exit(1)

    # 5. Dọn dẹp backup cũ
    logger.info(f"\n🧹 Dọn dẹp backup cũ hơn {keep_days} ngày...")
    deleted = cleanup_old_backups(keep_days)
    if deleted > 0:
        logger.info(f"   Đã xóa {deleted} bản backup cũ")
    else:
        logger.info("   Không có backup cũ cần xóa")

    # 6. Liệt kê backup hiện có
    backups = list_existing_backups()
    logger.info(f"\n📋 Danh sách backup hiện có ({len(backups)} bản):")
    for b in backups:
        logger.info(f"   • {b['name']} ({b['size_kb']:.1f} KB) - {b['created'].strftime('%Y-%m-%d %H:%M')}")

    logger.info("\n" + "=" * 60)
    logger.info("✅ SAO LƯU HOÀN TẤT!")
    logger.info("=" * 60)


# ============================================
# ENTRY POINT
# ============================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Backup cơ sở dữ liệu VCFE Database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  python scripts/backup_db.py                    # Backup với cấu hình mặc định
  python scripts/backup_db.py --keep-days 14     # Giữ lại 14 ngày
  python scripts/backup_db.py --install-task      # Cài đặt tự động backup hàng ngày
        """
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help=f"Đường dẫn tới file database (mặc định: {DEFAULT_DB_NAME} trong thư mục gốc dự án)"
    )
    parser.add_argument(
        "--keep-days",
        type=int,
        default=DEFAULT_KEEP_DAYS,
        help=f"Số ngày giữ lại backup (mặc định: {DEFAULT_KEEP_DAYS})"
    )
    parser.add_argument(
        "--install-task",
        action="store_true",
        help="Cài đặt Windows Task Scheduler để tự động backup hàng ngày lúc 02:00"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Chỉ liệt kê các bản backup hiện có"
    )

    args = parser.parse_args()

    if args.install_task:
        install_windows_task()
    elif args.list:
        backups = list_existing_backups()
        if backups:
            print(f"\n📋 Backup hiện có ({len(backups)} bản):")
            for b in backups:
                print(f"  • {b['name']} ({b['size_kb']:.1f} KB) - {b['created'].strftime('%Y-%m-%d %H:%M')}")
        else:
            print("\n💡 Chưa có bản backup nào.")
    else:
        run_backup(db_path_str=args.db_path, keep_days=args.keep_days)
