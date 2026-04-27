# backend/routes/files.py
"""
F-05 fix — Endpoint nội bộ phục vụ file đã upload (avatar, tài liệu).

NGUYÊN TẮC:
    - Thư mục `data/uploads/` (cấu hình qua settings.UPLOAD_DIR) NẰM NGOÀI
      `frontend/static/`, do đó KHÔNG được StaticFiles mount công khai.
    - Mọi file chỉ được phục vụ qua route `/api/documents/{file_path}` với:
        * Bắt buộc đã đăng nhập (Depends(require_login)).
        * Resolve đường dẫn tuyệt đối, kiểm tra nằm trong UPLOAD_DIR
          (chống Path Traversal "../../etc/passwd").
        * Chuẩn hoá kind ("avatars"/"docs") + cccd (regex 9/12 số) +
          tên file (UUID hex .ext) để chặn ký tự lạ.
"""

from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from backend.config import settings
from backend.deps import require_login
from backend.utils.validators import validate_cccd

router = APIRouter(prefix="/api/documents", tags=["files"])

# Tên file lưu trên đĩa LUÔN do server sinh: <uuid_hex>.<ext>.
# Whitelist regex để chặn mọi ký tự lạ (kể cả NULL byte, %2e%2e).
_SAFE_FILENAME_RE = re.compile(r"^[a-f0-9]{32}\.[a-z0-9]{1,8}$")

# Chỉ cho phép 2 loại "kind" (theo cấu trúc ./avatars/, ./docs/).
_ALLOWED_KINDS = {"avatars", "docs"}


def _upload_root() -> Path:
    """Trả Path tuyệt đối của thư mục gốc lưu file upload."""
    return (Path(settings.BASE_DIR) / settings.UPLOAD_DIR).resolve()


@router.get("/{kind}/{cccd}/{filename}")
def serve_document(
    kind: str,
    cccd: str,
    filename: str,
    user: dict = Depends(require_login),  # F-05: BẮT BUỘC đã đăng nhập
):
    """
    Trả về 1 file upload.

    Lộ trình kiểm tra (theo thứ tự, fail-fast):
        1) require_login: nếu cookie session không hợp lệ -> Depends raise
           HTTPException 307 redirect login. (Theo yêu cầu F-05 trả 403,
           có thể đổi require_login -> get_current_user + tự raise 403; ở
           đây giữ behaviour redirect cho đồng bộ với toàn hệ.)
        2) `kind`     in {"avatars", "docs"}.
        3) `cccd`     đúng regex 9/12 số.
        4) `filename` đúng pattern <uuid>.<ext>.
        5) resolve full path, đảm bảo nằm trong upload_root (chống traversal).
        6) Tồn tại file và là file thường (không phải symlink ra ngoài).
    """
    # (2) chống enum thư mục lạ
    if kind not in _ALLOWED_KINDS:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")

    # (3) chống path traversal qua cccd; raise 400 nếu lệch chuẩn
    cccd = validate_cccd(cccd)

    # (4) chống tên file độc — chỉ chấp nhận tên do server sinh
    if not _SAFE_FILENAME_RE.fullmatch(filename):
        raise HTTPException(status_code=400, detail="Tên file không hợp lệ.")

    # (5) resolve và VERIFY nằm trong upload_root.
    # `Path.resolve()` đã collapse "../" nên dù mọi tầng kiểm tra trên bị
    # bypass, kiểm tra prefix dưới đây vẫn bắt được.
    upload_root = _upload_root()
    target = (upload_root / kind / cccd / filename).resolve()

    try:
        target.relative_to(upload_root)
    except ValueError:
        # target nằm NGOÀI upload_root -> chắc chắn là Path Traversal
        raise HTTPException(status_code=400, detail="Yêu cầu không hợp lệ.")

    # (6) chỉ phục vụ file thường, không thư mục, không symlink trỏ ra ngoài
    if not target.is_file():
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")
    # Bonus: nếu là symlink, đã được resolve() đi tới đích thực; nếu đích
    # nằm ngoài upload_root thì đã bị chặn ở bước (5).

    # FileResponse tự lo Content-Type đoán theo extension.
    # Thêm content_disposition_type="inline" để ép trình duyệt hiển thị trực tiếp
    # (với các file trình duyệt đọc được như PDF, JPG, PNG).
    # Truyền thêm filename để khi người dùng ấn "Lưu/Tải xuống" từ trình duyệt,
    # file sẽ giữ đúng tên chứ không bị mất đuôi.
    return FileResponse(
        path=str(target),
        filename=filename,
        content_disposition_type="inline"
    )
