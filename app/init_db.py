
import logging
from app.db.session import engine
from app.db.base import Base
# Import models to register them with metadata
from app.models.models import User, DoiTuong, LienHe, TaiChinh, PhuongTien, NhanThan, HoSoDacThu, TaiLieu, QuaTrinhHoatDong, NguonDuLieu, QuanHeDoiTuong, AuditLog

logger = logging.getLogger(__name__)


def init_db():
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise e
