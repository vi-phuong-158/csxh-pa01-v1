# backend/security.py
"""
Tiện ích bảo mật cấp ứng dụng:
    - Session token (đã có): ký user_id bằng itsdangerous TimestampSigner.
    - CSRF token (F-10):     stateless, signed bằng URLSafeTimedSerializer
      với salt riêng "csrf". Không cần lưu state ở server.

THIẾT KẾ CSRF (PHƯƠNG ÁN STATELESS):
    - Khi client GET 1 trang HTML, server đặt cookie `csrf_token` (httponly=False
      để JS đọc được giá trị nhúng vào header HTMX) — xem `backend/main.py`.
    - Mỗi POST/PUT/PATCH/DELETE phải kèm token đó qua HEADER `X-CSRF-Token`
      (HTMX/AJAX) HOẶC trường form ẩn `_csrf` (form HTML thuần như login).
    - Server xác minh chữ ký + max_age — không so với cookie nữa, vì chỉ
      server có SECRET_KEY mới mint được token hợp lệ -> attacker không
      thể giả mạo token.
    - SameSite=Lax + signed token = chặn được cross-site POST.
"""

from __future__ import annotations

import secrets

from itsdangerous import (
    BadSignature, SignatureExpired, TimestampSigner, URLSafeTimedSerializer,
)

from backend.config import settings

# -- Session signer (giữ nguyên hành vi cũ) --------------------------------
_signer = TimestampSigner(settings.SECRET_KEY, salt="session")

# -- CSRF signer (mới) ------------------------------------------------------
# salt riêng "csrf" để cùng SECRET_KEY nhưng namespace tách biệt với session,
# tránh nhầm lẫn token loại này thành token loại kia.
_csrf_signer = URLSafeTimedSerializer(settings.SECRET_KEY, salt="csrf")

# CSRF token tồn tại lâu hơn session để tránh "form mở 30 phút bị mất token"
# (vd cán bộ mở form rồi đi pha trà rồi quay lại submit). 8 giờ là an toàn
# vì token chỉ là chống CSRF, không cấp quyền.
CSRF_MAX_AGE = 8 * 60 * 60


# ===== SESSION =============================================================
def create_session_token(user_id: int) -> str:
    return _signer.sign(str(user_id)).decode()


def verify_session_token(token: str) -> int | None:
    try:
        value = _signer.unsign(token, max_age=settings.SESSION_MAX_AGE)
        return int(value.decode())
    except (BadSignature, SignatureExpired, ValueError):
        return None


# ===== CSRF (F-10) =========================================================
def issue_csrf_token() -> str:
    """
    Sinh CSRF token mới: ký 1 nonce ngẫu nhiên 16 byte bằng SECRET_KEY.

    - nonce ngẫu nhiên: chống replay (mỗi token unique).
    - URLSafeTimedSerializer: ra chuỗi an toàn cho cookie/header.
    """
    nonce = secrets.token_urlsafe(16)
    return _csrf_signer.dumps(nonce)


def verify_csrf_token(token: str | None, max_age: int = CSRF_MAX_AGE) -> bool:
    """
    Trả True nếu token đúng chữ ký SECRET_KEY và chưa quá hạn.
    Trả False với mọi loại lỗi (signature, expired, không phải string).
    """
    if not isinstance(token, str) or not token:
        return False
    try:
        _csrf_signer.loads(token, max_age=max_age)
        return True
    except (BadSignature, SignatureExpired):
        return False
    except Exception:
        # Defensive: bất kỳ lỗi parse nào cũng coi là không hợp lệ
        return False
