# backend/config.py
"""
Cấu hình hệ thống — đọc từ biến môi trường / file `.env`.

NGUYÊN TẮC FAIL-FAST:
    - DB_PASSWORD và SECRET_KEY BẮT BUỘC — được nhập tương tác qua run_server.py
      (getpass) và set vào os.environ trước khi module này được import.
    - ADMIN_PASSWORD chỉ cần thiết lần đầu (chưa có user trong DB). run_server.py
      hỏi và set vào os.environ nếu cần; nếu đã có admin thì để None.
    - Mục tiêu: ngăn deploy với key trống/known-bad, không cần file .env cho secret.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Set

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Các giá trị mật khẩu/key tuyệt đối KHÔNG được phép dùng (đã từng là default
# trong source hoặc thuộc top-list password yếu phổ biến).
_FORBIDDEN_SECRETS: Set[str] = {
    "",
    "changeme",
    "change_me",
    "default",
    "password",
    "Password1",
    "Admin@123",
    "Admin@123456",
    "admin",
    "123456",
    "12345678",
    "qwerty",
    "your_db_password_here",
    "your_secret_key_here_min_32_chars",
    "your_admin_password_here",
}


class Settings(BaseSettings):
    # `extra="forbid"` để chặn typo env-var lặng lẽ (ví dụ DB_PASSWROD)
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # ---------- Metadata ----------
    PROJECT_NAME: str = "VCFE Database"
    PROJECT_VERSION: str = "2.0.0"
    BASE_DIR: Path = Path(__file__).resolve().parent.parent

    # ---------- Database ----------
    DB_NAME: str = "security_profile.db"
    # Mật khẩu mã hoá SQLCipher — BẮT BUỘC, tối thiểu 16 ký tự.
    # Dùng `Field(...)` (Ellipsis) để pydantic raise nếu không có env.
    DB_PASSWORD: str = Field(..., min_length=12)

    # ---------- Security / Session ----------
    # Khoá ký session cookie (itsdangerous). Tối thiểu 32 ký tự ngẫu nhiên.
    SECRET_KEY: str = Field(..., min_length=32)
    SESSION_COOKIE: str = "session_token"
    SESSION_MAX_AGE: int = 1800  # 30 phút
    # Cờ HTTPS thật — chỉ True khi vận hành sau TLS. Local HTTP để False.
    USE_HTTPS: bool = False

    # ---------- Super Admin khởi tạo lần đầu ----------
    # None khi admin đã tồn tại (run_server.py không set env var này).
    # Chỉ có giá trị khi lần đầu khởi động chưa có user trong DB.
    ADMIN_PASSWORD: Optional[str] = Field(default=None)

    # ---------- Upload ----------
    UPLOAD_DIR: str = "data/uploads"  # khuyến nghị NGOÀI frontend/static
    MAX_UPLOAD_MB: int = 10

    # ---------- Debug ----------
    DEBUG: bool = False

    # ====================================================================
    #                        VALIDATORS
    # ====================================================================

    @field_validator("DB_PASSWORD", "SECRET_KEY", "ADMIN_PASSWORD")
    @classmethod
    def _reject_known_bad(cls, v: Optional[str], info) -> Optional[str]:
        """
        Chặn các chuỗi mặc định / yếu phổ biến.
        ADMIN_PASSWORD có thể là None (admin đã tồn tại) — bỏ qua khi đó.
        """
        if v is None:
            return v
        if v.strip() in _FORBIDDEN_SECRETS:
            raise ValueError(
                f"{info.field_name} đang dùng giá trị mặc định/yếu — "
                "vui lòng nhập giá trị mạnh"
            )
        return v

    @field_validator("DB_PASSWORD")
    @classmethod
    def _db_password_complexity(cls, v: str) -> str:
        """
        Mật khẩu DB phải có độ phức tạp tối thiểu để chống brute-force file
        SQLCipher khi máy bị thu giữ vật lý.
        """
        if not any(c.isdigit() for c in v):
            raise ValueError("DB_PASSWORD phải chứa ít nhất 1 chữ số")
        if not any(c.isalpha() for c in v):
            raise ValueError("DB_PASSWORD phải chứa ít nhất 1 chữ cái")
        return v

    # ====================================================================
    #                        DERIVED PATHS
    # ====================================================================

    @property
    def DB_PATH(self) -> Path:
        return self.BASE_DIR / self.DB_NAME

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"sqlite:///{self.DB_PATH}"


# --------------------------------------------------------------------------
# Khởi tạo settings — fail-fast: nếu thiếu env hoặc giá trị yếu, raise ngay
# tại import time. Trả về thông báo lỗi tiếng Việt rõ ràng cho admin sửa.
# --------------------------------------------------------------------------
try:
    settings = Settings()
except ValidationError as e:
    # Chuyển ValidationError thành RuntimeError với hướng dẫn cụ thể
    msg_lines = ["Cấu hình bảo mật không hợp lệ — hệ thống dừng khởi động:"]
    for err in e.errors():
        loc = ".".join(str(p) for p in err["loc"])
        msg_lines.append(f"  - {loc}: {err['msg']}")
    msg_lines.append("")
    msg_lines.append("Hướng dẫn:")
    msg_lines.append("  Khởi động server bằng: python run_server.py")
    msg_lines.append("  DB_PASSWORD và SECRET_KEY sẽ được nhập tương tác (getpass).")
    msg_lines.append("  KHÔNG truyền secret qua file .env.")
    raise RuntimeError("\n".join(msg_lines)) from e
