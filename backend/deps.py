from typing import Optional, Generator
from fastapi import Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from backend.config import settings
from backend.db.session import get_db
from backend.security import verify_session_token
from backend.models.models import User


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
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    return user


def _redirect_to_login(request: Request):
    from fastapi import HTTPException
    from starlette.responses import RedirectResponse
    next_url = str(request.url)
    return HTTPException(
        status_code=307,
        headers={"Location": f"/auth/login?next={next_url}"},
    )
