import atexit
import sqlite3
import logging
from sqlalchemy import create_engine, event, text
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker, Session
from backend.config import settings

logger = logging.getLogger(__name__)

# Thử dùng sqlcipher3 nếu có, nếu không fallback sang sqlite3 tiêu chuẩn
try:
    from sqlcipher3 import dbapi2 as _sqlite_module
    USE_SQLCIPHER = True
    logger.info("Sử dụng sqlcipher3 (mã hóa DB)")
except ImportError:
    _sqlite_module = sqlite3
    USE_SQLCIPHER = False
    logger.warning("sqlcipher3 không khả dụng — dùng sqlite3 tiêu chuẩn (DB KHÔNG mã hóa)")


def _get_engine():
    engine = create_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        if USE_SQLCIPHER:
            cursor.execute(f"PRAGMA key='{settings.DB_PASSWORD}';")
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA journal_mode=WAL;")
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
    from backend.models.models import Base  # noqa: F401
    Base.metadata.create_all(bind=engine)


@atexit.register
def _checkpoint():
    try:
        with engine.connect() as conn:
            conn.execute(text("PRAGMA wal_checkpoint(TRUNCATE);"))
    except Exception:
        pass
