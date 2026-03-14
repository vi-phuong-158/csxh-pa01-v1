
import os
import secrets
from pathlib import Path


class Settings:
    PROJECT_NAME: str = "Security Profile 360"
    PROJECT_VERSION: str = "2.0.0"

    # Base directory
    BASE_DIR = Path(__file__).resolve().parent.parent.parent

    # Database
    DB_NAME = "security_profile.db"
    SQLALCHEMY_DATABASE_URI: str = f"sqlite:///{BASE_DIR}/{DB_NAME}"

    # Security
    # SECRET_KEY phải được cung cấp qua biến môi trường.
    # Nếu không có, sinh tạm một key ngẫu nhiên cho phiên hiện tại
    _env_secret = os.getenv("SECRET_KEY")
    if _env_secret:
        SECRET_KEY: str = _env_secret
    else:
        # Sinh key ngẫu nhiên an toàn, không log ra ngoài
        SECRET_KEY: str = secrets.token_urlsafe(32)

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


settings = Settings()
