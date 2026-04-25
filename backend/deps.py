# backend/deps.py
"""
FastAPI Dependencies dùng chung:
    - get_current_user / require_login / require_admin: xác thực phiên.
    - csrf_protect (F-10): xác thực CSRF token cho mọi request đổi state.
    - require_profile_access (F-14): kiểm tra quyền xem/sửa hồ sơ theo
      cột `nguoi_phu_trach_id`.
"""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.config import settings
from backend.db.session import get_db
from backend.models.models import DoiTuong, User
from backend.security import verify_csrf_token, verify_session_token
from backend.utils.validators import validate_cccd


# ============================================================================
# Authentication
# ============================================================================
def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[dict]:
    token = request.cookies.get(settings.SESSION_COOKIE)
    if not token:
        return None
    user_id = verify_session_token(token)
    if not user_id:
        return None
    user = db.get(User, user_id)
    if not user or not user.is_active:
        return None
    return {
        "id": user.id,
        "username": user.username,
        "ho_ten": user.ho_ten or user.username,
        "role": user.role,
        "must_change_password": bool(user.must_change_password),
    }


def require_login(
    request: Request,
    user: Optional[dict] = Depends(get_current_user),
):
    if user is None:
        raise _redirect_to_login(request)
    return user


def require_admin(
    user: dict = Depends(require_login),
):
    if user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    return user


def _redirect_to_login(request: Request) -> HTTPException:
    next_url = str(request.url)
    return HTTPException(
        status_code=307,
        headers={"Location": f"/auth/login?next={next_url}"},
    )


# ============================================================================
# F-10: CSRF Protect
# ============================================================================
# Các method ĐỔI TRẠNG THÁI cần kiểm CSRF. GET/HEAD/OPTIONS thì không.
_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Một số endpoint cần được loại trừ vì client chưa có cookie/token thời điểm gọi:
#   - POST /auth/login: lần đầu user submit, sẽ kiểm CSRF qua token TỪ TRANG GET
#     (ta vẫn enforce vì server đã set cookie csrf khi user GET /auth/login).
# Do server LUÔN set cookie csrf trên mọi GET response (xem main.py middleware),
# kể cả GET /auth/login đã có token sẵn — nên KHÔNG cần exclude bất cứ route nào.
# Hằng dưới giữ lại cho trường hợp tương lai cần whitelist (vd webhook nội bộ).
_CSRF_EXEMPT_PATHS: set[str] = set()


async def csrf_protect(request: Request) -> None:
    """
    Dependency áp chung toàn ứng dụng (qua app-level Depends).

    Quy trình:
        1) Method an toàn -> return ngay (GET, HEAD, OPTIONS).
        2) Path nằm trong whitelist -> bỏ qua.
        3) Đọc token từ HEADER `X-CSRF-Token` trước (HTMX mặc định).
        4) Nếu không có header, đọc từ FORM field `_csrf` (form HTML).
        5) verify_csrf_token() -> nếu không hợp lệ -> 403.
    """
    if request.method not in _UNSAFE_METHODS:
        return

    if request.url.path in _CSRF_EXEMPT_PATHS:
        return

    # 3) Header (HTMX/AJAX)
    token = request.headers.get("X-CSRF-Token") or request.headers.get("X-CSRFToken")

    # 4) Fallback: form field `_csrf` (chỉ khi content-type là form)
    if not token:
        ct = (request.headers.get("content-type") or "").lower()
        if "application/x-www-form-urlencoded" in ct or "multipart/form-data" in ct:
            # FastAPI cache form() — đọc ở đây không gãy handler sau.
            try:
                form = await request.form()
                raw = form.get("_csrf")
                token = str(raw) if raw is not None else None
            except Exception:
                token = None

    if not verify_csrf_token(token):
        # Trả 403 chứ KHÔNG redirect — để fail hiển thị rõ ràng cho user/dev.
        raise HTTPException(
            status_code=403,
            detail="CSRF token không hợp lệ hoặc đã hết hạn. Vui lòng tải lại trang.",
        )


# ============================================================================
# F-14: Phân quyền truy cập hồ sơ
# ============================================================================
def require_profile_access(
    cccd: str,
    user: dict = Depends(require_login),
    db: Session = Depends(get_db),
) -> dict:
    """
    Đảm bảo `user` được phép xem/sửa hồ sơ `cccd`.

    Quy tắc:
        - Super Admin (role == "super_admin") -> truy cập TẤT CẢ hồ sơ.
        - User thường:
            * Hồ sơ chưa phân công (nguoi_phu_trach_id IS NULL) -> được xem
              (giúp dữ liệu cũ chưa migrate vẫn dùng được; admin nên gán
              người phụ trách càng sớm càng tốt).
            * Hồ sơ đã phân công -> chỉ xem nếu nguoi_phu_trach_id == user.id.
        - cccd không tồn tại -> 404 (giấu thông tin).

    Trả về dict user (giống require_login) để route chain tiếp.
    """
    cccd = validate_cccd(cccd)

    # Super admin: full access — không cần truy DB
    if user.get("role") == "super_admin":
        return user

    dt = db.get(DoiTuong, cccd)
    if dt is None:
        # 404 (không phải 403) để không leak sự tồn tại của cccd
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ.")

    owner_id = getattr(dt, "nguoi_phu_trach_id", None)

    if owner_id is None:
        # Chưa phân công -> coi như công khai trong nội bộ. Đây là quyết
        # định CÓ Ý THỨC để không phá dữ liệu cũ. Nếu muốn chính sách
        # "default-deny", đổi `return user` -> raise HTTPException(403, ...)
        return user

    if owner_id != user["id"]:
        raise HTTPException(
            status_code=403,
            detail="Bạn không có quyền truy cập hồ sơ này (không thuộc danh sách phụ trách).",
        )

    return user
