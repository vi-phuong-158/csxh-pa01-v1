from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from backend.config import settings
from backend.db.session import get_db
from backend.deps import get_current_user, require_login
from backend.security import create_session_token
from backend.services import auth as auth_svc
from backend.limiter import limiter

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="frontend/templates")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, next: str = "/dashboard", user=Depends(get_current_user)):
    if user:
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse(request, "auth/login.html", {"next": next, "error": None})


@router.post("/login")
@limiter.limit("5/minute")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form("/dashboard"),
    db: Session = Depends(get_db),
):
    user = auth_svc.authenticate(db, username, password)
    if not user:
        return templates.TemplateResponse(
            request, "auth/login.html",
            {"next": next, "error": "Tên đăng nhập hoặc mật khẩu không đúng, hoặc tài khoản bị khóa"},
            status_code=401,
        )

    token = create_session_token(user["id"])
    redirect_url = "/auth/change-password" if user["must_change_password"] else next
    response = RedirectResponse(redirect_url, status_code=302)
    response.set_cookie(
        key=settings.SESSION_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=settings.SESSION_MAX_AGE,
    )
    return response


@router.post("/logout")
def logout(request: Request):
    response = RedirectResponse("/auth/login", status_code=302)
    response.delete_cookie(settings.SESSION_COOKIE)
    return response


@router.get("/change-password", response_class=HTMLResponse)
def change_password_page(request: Request, user=Depends(require_login)):
    return templates.TemplateResponse(request, "auth/change_password.html", {"user": user, "error": None, "success": None})


@router.post("/change-password")
async def change_password_submit(
    request: Request,
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    user: dict = Depends(require_login),
    db: Session = Depends(get_db),
):
    if new_password != confirm_password:
        return templates.TemplateResponse(
            request, "auth/change_password.html",
            {"user": user, "error": "Mật khẩu xác nhận không khớp", "success": None},
        )
    ok, msg = auth_svc.change_password(db, user["id"], new_password)
    if not ok:
        return templates.TemplateResponse(
            request, "auth/change_password.html",
            {"user": user, "error": msg, "success": None},
        )
    return RedirectResponse("/dashboard", status_code=302)
