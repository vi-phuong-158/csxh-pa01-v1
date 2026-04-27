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
    pwd = os.environ.get("QLNNN_DB_PASSPHRASE", "")
    if pwd:
        logger.info("DB_PASSPHRASE đọc từ biến môi trường runtime.")
        return pwd

    # (b) File .env — bỏ qua nếu có cờ --no-env.
    if not no_env:
        # Import muộn để tận dụng logic đọc file đã có sẵn ở config.
        from backend.config import _read_env_file_value, ENV_DB_PASSPHRASE, ENV_FILE_PATH
        pwd = _read_env_file_value(ENV_DB_PASSPHRASE)
        if pwd:
            logger.info(f"DB_PASSPHRASE đọc từ file: {ENV_FILE_PATH}")
            # Cảnh báo quyền file (chỉ trên Linux/Unix; Windows có cơ chế ACL riêng).
            try:
                if hasattr(os, "stat") and ENV_FILE_PATH.exists():
                    mode = ENV_FILE_PATH.stat().st_mode & 0o777
                    if os.name != "nt" and mode & 0o077:
                        logger.warning(
                            f"⚠ File .env có quyền {oct(mode)} — group/other có thể đọc. "
                            f"Khuyến nghị: chmod 600 {ENV_FILE_PATH}"
                        )
            except Exception:
                pass
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
    os.environ["QLNNN_DB_PASSPHRASE"] = pwd
    pwd = None  # noqa: F841 — xóa biến local để giảm dấu vết RAM.

    # 2. Verify (mở thử DB). Phải import SAU khi env đã set.
    from backend.database import verify_or_init_db_key
    from backend.create_tables import init_db
    from backend.auth_service import init_super_admin_if_needed

    try:
        status = verify_or_init_db_key()
    except RuntimeError as e:
        sys.exit(f"[Bootstrap] {e}")
    logger.info(f"DB key OK ({status}). Khởi tạo schema...")

    # 3. Tạo schema (idempotent).
    init_db()

    # 4. Khởi tạo Super Admin nếu là lần đầu.
    init_super_admin_if_needed()

    # 5. Khởi động uvicorn.
    logger.info("Khởi động Uvicorn tại http://127.0.0.1:9000 ...")
    import uvicorn
    from backend.main import app  # import object thay vì chuỗi — bắt buộc khi đóng gói PyInstaller
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=9000,
        reload=False,        # Vá H1: tuyệt đối KHÔNG reload trong production.
        workers=1,           # SQLite single-writer.
        log_level="info",
        server_header=False, # Không lộ phiên bản uvicorn.
    )


if __name__ == "__main__":
    main()
