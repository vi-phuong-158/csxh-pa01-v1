# backend/db/session.py
"""
Khởi tạo SQLAlchemy engine cho SQLCipher.

CÁC RỦI RO ĐÃ ĐƯỢC XỬ LÝ Ở FILE NÀY:
    F-02 (CRITICAL): Lỗi SQL Injection vào câu lệnh `PRAGMA key='...'`
        - SQLCipher KHÔNG hỗ trợ parameter binding cho PRAGMA, nên bắt buộc
          phải escape thủ công ký tự nháy đơn (' -> '').
        - Sau khi set key, query thử `sqlite_master` ngay trong handler để
          fail-fast nếu key sai (tránh fail-open mở DB như SQLite thuần).
    F-02b (CRITICAL — phát hiện thêm khi self-test):
        - SQLAlchemy với URL `sqlite:///...` MẶC ĐỊNH dùng module `sqlite3`
          chuẩn của stdlib, KHÔNG phải `sqlcipher3` dù ta đã `import`.
        - Hậu quả: PRAGMA key chạy trên SQLite thường (vô tác dụng) -> file
          DB sinh ra ở dạng plaintext (`SQLite format 3` header).
        - Khắc phục: truyền `module=sqlcipher3.dbapi2` vào `create_engine`
          để SQLAlchemy gọi đúng DBAPI có hỗ trợ encryption.
    F-03 (CRITICAL): Đảm bảo DB_PASSWORD được validate fail-fast tại
        `backend/config.py` — file này chỉ tin dùng giá trị đã validate.
"""

from __future__ import annotations

import atexit
import logging

# BẮT BUỘC dùng sqlcipher3 — không fallback sang sqlite3 chuẩn vì sẽ làm
# PRAGMA key bị bỏ qua, dữ liệu sẽ KHÔNG được mã hoá at-rest.
from sqlcipher3 import dbapi2 as sqlcipher_dbapi

from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from backend.config import settings

logger = logging.getLogger(__name__)


def _escape_sqlcipher_key(raw: str) -> str:
    """
    Escape ký tự nháy đơn cho `PRAGMA key='...'`.

    SQLite/SQLCipher cú pháp string literal: ' bên trong chuỗi -> ''.
    Nếu không escape, mật khẩu chứa dấu ' sẽ làm break PRAGMA, dẫn tới
    SQLCipher coi như chưa set key -> mở file ở chế độ không mã hoá
    (silent fail) HOẶC raise lỗi runtime khó debug.

    Đây là biện pháp phòng thủ thứ 1. Biện pháp thứ 2 là `_verify_key()`
    bên dưới: query thử để chắc key đúng.
    """
    return raw.replace("'", "''")


def _verify_key(cursor) -> None:
    """
    Sau khi set PRAGMA key, query thử bảng metadata.
    Nếu key sai (hoặc bị bypass), SQLCipher raise `DatabaseError: file is
    not a database` — fail-fast ngay tại lúc connect.
    """
    cursor.execute("SELECT count(*) FROM sqlite_master;")
    cursor.fetchone()


def _get_engine():
    engine = create_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        # F-02b: ép SQLAlchemy gọi sqlcipher3 thay vì sqlite3 chuẩn của Python.
        # Nếu thiếu tham số này, dialect "sqlite" sẽ tự import stdlib sqlite3
        # khiến PRAGMA key vô hiệu và DB lưu ở dạng plaintext.
        module=sqlcipher_dbapi,
        connect_args={"check_same_thread": False, "timeout": 30},
        # NullPool: mỗi request mở kết nối mới -> handler `connect` chạy lại
        # PRAGMA key. Đảm bảo không có connection nào "rò" mà không có key.
        poolclass=NullPool,
    )

    @event.listens_for(engine, "connect")
    def set_sqlcipher_pragma(dbapi_connection, connection_record):
        """
        Mỗi lần SQLAlchemy mở connection mới: nạp key, kiểm tra hợp lệ,
        sau đó bật khoá ngoại + journal mode.
        """
        cursor = dbapi_connection.cursor()
        try:
            # F-02 fix: escape thủ công vì PRAGMA không bind tham số được
            safe_key = _escape_sqlcipher_key(settings.DB_PASSWORD)
            cursor.execute(f"PRAGMA key='{safe_key}';")

            # F-16: PIN cipher params về SQLCipher 4 defaults RÕ RÀNG.
            # Lý do: nếu sau này nâng cấp lên SQLCipher 5+ với defaults
            # khác (kdf_iter cao hơn, hmac khác), DB cũ có thể không mở
            # được. Khi pin, ta luôn đọc/ghi cùng định dạng dù version
            # binary thay đổi.
            #
            # PRAGMA cipher_compatibility = 4: tương đương "SQLCipher 4
            # default" preset, ép page_size=4096, kdf_iter=256000,
            # hmac_algorithm=HMAC_SHA512, kdf_algorithm=PBKDF2_HMAC_SHA512.
            # Đây là 1 lệnh thay thế bộ pragma chi tiết, hoạt động trên
            # cả SQLCipher 4.x và 5.x.
            cursor.execute("PRAGMA cipher_compatibility = 4;")

            # Verify ngay — nếu file DB cũ tồn tại nhưng key sai sẽ raise
            try:
                _verify_key(cursor)
            except sqlcipher_dbapi.DatabaseError as e:
                # Không log raw key; chỉ thông báo nguyên nhân
                logger.error("Mở SQLCipher thất bại: DB_PASSWORD không khớp với file DB hiện có.")
                raise RuntimeError(
                    "Không mở được database — DB_PASSWORD trong .env không khớp "
                    "với mật khẩu đã dùng khi tạo file DB. Kiểm tra lại .env "
                    "hoặc khôi phục file DB từ backup phù hợp."
                ) from e

            cursor.execute("PRAGMA foreign_keys = ON;")
            cursor.execute("PRAGMA journal_mode=WAL;")
        finally:
            cursor.close()

    return engine


engine = _get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Tạo các bảng nếu chưa có. Cũng là điểm kiểm tra fail-fast lần đầu:
    nếu PRAGMA key sai, lệnh `create_all` sẽ raise.

    F-14: chạy auto-migrate idempotent cho các cột mới được thêm sau lần
    deploy đầu tiên (vì `create_all` không tự ALTER bảng đã tồn tại).
    """
    from backend.models.models import Base  # noqa: F401

    try:
        Base.metadata.create_all(bind=engine)
        _auto_migrate()
    except DatabaseError as e:
        # Bao bọc lại để stack trace ngắn gọn cho admin
        raise RuntimeError(
            "Khởi tạo database thất bại — kiểm tra DB_PASSWORD hoặc tính toàn vẹn "
            "của file DB."
        ) from e


# ============================================================================
# F-14: auto-migrate idempotent — thêm cột mới mà không phá DB cũ
# ============================================================================
# Danh sách (table, column, ddl). Mỗi entry chạy 1 lần; nếu cột đã có thì
# bỏ qua. Khi thêm cột mới trong tương lai chỉ cần append vào list.
_PENDING_COLUMNS: list[tuple[str, str, str]] = [
    # F-14: gán cán bộ phụ trách hồ sơ
    ("doi_tuong", "nguoi_phu_trach_id", "INTEGER REFERENCES users(id) ON DELETE SET NULL"),
]


def _auto_migrate() -> None:
    """
    Quét `_PENDING_COLUMNS` và ALTER TABLE nếu cột chưa tồn tại.
    Dùng PRAGMA table_info để check tồn tại — chuẩn SQLite/SQLCipher.
    """
    with engine.connect() as conn:
        for table, col, ddl in _PENDING_COLUMNS:
            rows = conn.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()
            existing_cols = {r[1] for r in rows}  # row[1] = name
            if col in existing_cols:
                continue
            logger.info("Auto-migrate: ALTER TABLE %s ADD COLUMN %s", table, col)
            conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}")
            conn.commit()


@atexit.register
def _checkpoint():
    """
    Khi process tắt êm: flush WAL về file chính để tránh để lại file `-wal`
    chứa transaction chưa commit. SQLCipher mã hoá cả WAL nên không lộ
    plaintext, nhưng checkpoint giúp file gọn và dễ backup.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("PRAGMA wal_checkpoint(TRUNCATE);"))
    except Exception:
        # Không dùng bare except: chỉ swallow để atexit không spam stderr
        pass
