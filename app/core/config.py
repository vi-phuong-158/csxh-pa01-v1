
import os
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
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-change-me")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


settings = Settings()
