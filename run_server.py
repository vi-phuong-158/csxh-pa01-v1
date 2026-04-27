"""
run_server.py
=============
Entry-point DUY NHẤT để khởi động hệ thống QLNNN.

Quy trình khởi động:
  1. Lấy DB_PASSPHRASE theo thứ tự:
        a. Biến môi trường QLNNN_DB_PASSPHRASE (cho test/auto-deploy)
        b. File .env ở thư mục gốc dự án (CHẾ ĐỘ MẶC ĐỊNH cho vận hành)
        c. Hỏi tương tác qua getpass (fallback an toàn)
     Cờ `--no-env` ép bỏ qua bước b và bắt phải nhập tay (cho đơn vị có két sắt).
     Cờ `--no-prompt` cấm hỏi tương tác (cho test/CI).
  2. Verify passphrase bằng cách thử mở DB → sai pass thì exit ngay,
     KHÔNG để uvicorn boot lên rồi mới fail request đầu.
  3. Tạo schema (idempotent).
  4. Tạo Super Admin nếu là lần đầu (interactive prompt mật khẩu admin).
  5. Khởi động Uvicorn (no reload, 1 worker, không lộ Server header).

Cách chạy thông thường:
    python run_server.py

Bắt nhập tay mật khẩu CSDL (bỏ qua .env):
    python run_server.py --no-env

Unattended (test/script):
    QLNNN_DB_PASSPHRASE='matkhau' QLNNN_BOOTSTRAP_ADMIN_PASSWORD='Adm!n123' \
        python run_server.py --no-prompt
"""
import os
import sys
import io
import getpass
import logging

# Force UTF-8 cho console Windows — ngăn UnicodeEncodeError với ký tự tiếng Việt.
# Phải chạy TRƯỚC mọi lệnh print/logging.
if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("qlnnn.bootstrap")


def _prompt_db_passphrase() -> str:
    """Hỏi DB_PASSPHRASE 1 lần (không xác nhận); ≥8 ký tự để chống fat-finger."""
    print("=" * 60)
    print(" HỆ THỐNG QUẢN LÝ NGƯỜI NƯỚC NGOÀI (QLNNN)")
    print(" Vui lòng nhập mật khẩu giải mã CSDL.")
    print(" (Mật khẩu sẽ KHÔNG hiển thị khi gõ.)")
    print("=" * 60)
    try:
        pwd = getpass.getpass(" DB Passphrase: ")
    except (EOFError, KeyboardInterrupt):
        sys.exit("\n[Bootstrap] Đã hủy.")
    if len(pwd) < 8:
        sys.exit("[Bootstrap] Passphrase quá ngắn (<8 ký tự). Hủy khởi động.")
    return pwd


def _resolve_db_passphrase(no_env: bool, no_prompt: bool) -> str:
    """
    Áp dụng quy tắc ưu tiên: env runtime → file .env → prompt.
    Trả về passphrase đã được xác định, hoặc exit nếu không lấy được.
    """
    # (a) Env runtime — luôn ưu tiên cao nhất, không phụ thuộc cờ.
    pwd = os.environ.get("DB_PASSWORD", "")
    if pwd:
        logger.info("DB_PASSWORD đọc từ biến môi trường runtime.")
        return pwd

    # (b) File .env — bỏ qua nếu có cờ --no-env.
    if not no_env:
        from dotenv import dotenv_values
        env_path = os.path.join(os.getcwd(), ".env")
        if os.path.exists(env_path):
            env_vars = dotenv_values(env_path)
            pwd = env_vars.get("DB_PASSWORD", "")
            if pwd:
                logger.info(f"DB_PASSWORD đọc từ file: {env_path}")
                return pwd

    # (c) Hỏi tương tác — bỏ qua nếu có cờ --no-prompt.
    if no_prompt:
        sys.exit(
            "[Bootstrap] --no-prompt đã bật nhưng không tìm thấy DB_PASSPHRASE "
            "ở env hay file .env. Hủy khởi động."
        )
    return _prompt_db_passphrase()


def main() -> None:
    no_env = "--no-env" in sys.argv
    no_prompt = "--no-prompt" in sys.argv

    # 1. Xác định DB_PASSPHRASE.
    pwd = _resolve_db_passphrase(no_env=no_env, no_prompt=no_prompt)

    # Đẩy vào env để các tầng config.py / database.py / auth_service.py đều thấy.
    os.environ["DB_PASSWORD"] = pwd
    pwd = None  # noqa: F841 — xóa biến local để giảm dấu vết RAM.

    # 2. Verify (mở thử DB). Phải import SAU khi env đã set.
    from backend.db.session import SessionLocal, init_db
    from backend.services.auth import init_super_admin

    try:
        # Việc khởi tạo SessionLocal sẽ trigger việc verify key trong session.py
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as e:
        sys.exit(f"[Bootstrap] Lỗi xác thực CSDL: {e}")
    logger.info("DB key OK. Khởi tạo schema...")

    # 3. Tạo schema (idempotent).
    init_db()

    # 4. Khởi tạo Super Admin nếu là lần đầu.
    db = SessionLocal()
    try:
        init_super_admin(db)
    finally:
        db.close()

    # 5. Khởi động uvicorn.
    port = 8000
    if "--port" in sys.argv:
        try:
            idx = sys.argv.index("--port")
            port = int(sys.argv[idx + 1])
        except (ValueError, IndexError):
            pass

    logger.info(f"Khởi động Uvicorn tại http://127.0.0.1:{port} ...")
    import uvicorn
    from backend.main import app
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        reload=False,
        workers=1,
        log_level="info",
        server_header=False,
    )


if __name__ == "__main__":
    from sqlalchemy import text # Thêm import text
    main()
