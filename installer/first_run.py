"""
first_run.py — Wizard tạo .env khi chạy lần đầu.

Tự động sinh DB_PASSWORD và SECRET_KEY an toàn bằng secrets module.
Chỉ yêu cầu người dùng đặt ADMIN_PASSWORD (tài khoản đăng nhập ứng dụng).
"""
import os
import secrets
import string
import sys
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent
ENV_PATH = APP_DIR / ".env"


def _generate_secret(length: int = 24) -> str:
    """Tạo chuỗi ngẫu nhiên có chữ + số, đủ phức tạp cho DB_PASSWORD."""
    alphabet = string.ascii_letters + string.digits
    while True:
        value = "".join(secrets.choice(alphabet) for _ in range(length))
        if any(c.isdigit() for c in value) and any(c.isalpha() for c in value):
            return value


def _prompt_admin_password() -> str:
    print()
    print("Tao tai khoan QUAN TRI VIEN (admin) cho he thong.")
    print("Mat khau phai co it nhat 12 ky tu, gom ca chu va so.")
    print()
    while True:
        pwd = input("  Nhap mat khau admin: ").strip()
        if len(pwd) < 12:
            print("  [LOI] Can it nhat 12 ky tu.\n")
            continue
        if not any(c.isdigit() for c in pwd):
            print("  [LOI] Can it nhat 1 chu so.\n")
            continue
        if not any(c.isalpha() for c in pwd):
            print("  [LOI] Can it nhat 1 chu cai.\n")
            continue
        confirm = input("  Nhap lai de xac nhan: ").strip()
        if pwd != confirm:
            print("  [LOI] Mat khau khong khop. Vui long thu lai.\n")
            continue
        return pwd


def main() -> None:
    print("=" * 52)
    print("   VCFE Database - Cai dat lan dau")
    print("=" * 52)
    print()
    print("He thong se tu dong tao khoa ma hoa co so du lieu")
    print("va khoa ky phien lam viec (an toan, ngau nhien).")
    print()

    admin_password = _prompt_admin_password()

    db_password  = _generate_secret(24)
    secret_key   = secrets.token_urlsafe(48)

    env_content = (
        "# VCFE Database - Cau hinh he thong\n"
        "# TAO TU DONG - KHONG CHIA SE FILE NAY\n"
        "\n"
        f"DB_PASSWORD={db_password}\n"
        f"SECRET_KEY={secret_key}\n"
        f"ADMIN_PASSWORD={admin_password}\n"
        "\n"
        "DEBUG=False\n"
        "USE_HTTPS=False\n"
        "SESSION_MAX_AGE=1800\n"
    )

    ENV_PATH.write_text(env_content, encoding="utf-8")

    print()
    print("[OK] File cau hinh da duoc tao.")
    print()
    print("Luu y: Khong xoa hoac chia se file .env —")
    print("       no chua mat khau ma hoa co so du lieu cua ban.")
    print()
    input("Nhan Enter de tiep tuc khoi dong ung dung...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[Da huy cai dat]")
        sys.exit(1)
    except Exception as exc:
        print(f"\n[LOI] {exc}")
        input("Nhan Enter de dong...")
        sys.exit(1)
