import secrets
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "VCFE Database"
    PROJECT_VERSION: str = "2.0.0"

    BASE_DIR: Path = Path(__file__).resolve().parent.parent

    # Database
    DB_NAME: str = "security_profile.db"
    DB_PASSWORD: str = "changeme"

    @property
    def DB_PATH(self) -> Path:
        return self.BASE_DIR / self.DB_NAME

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"sqlite:///{self.DB_PATH}"

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    SESSION_COOKIE: str = "session_token"
    SESSION_MAX_AGE: int = 1800  # 30 phút

    # Admin
    ADMIN_PASSWORD: str = "Admin@123456"

    # Upload
    UPLOAD_DIR: str = "frontend/static/uploads"
    MAX_UPLOAD_MB: int = 10

    DEBUG: bool = False


settings = Settings()
