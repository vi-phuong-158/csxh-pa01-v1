from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from backend.config import settings
from backend.db.session import get_db
from backend.deps import get_current_user, require_login
from backend.limiter import check_login_rate, reset_login_rate
from backend.security import create_session_token
from backend.services import auth as auth_svc
from backend.utils.validators import safe_next_url

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="frontend/templates")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, next: str = "/dashboard", user=Depends(get_current_user)):
    # F-09: chuẩn hoá next ngay khi nhận từ query string — nếu attacker chèn
    # ?next=https://evil.com, sẽ bị quy về "/dashboard".
    safe_next = safe_next_url(next, default="/dashboard")
    if user:
        return RedirectResponse(safe_next, status_code=302)
    return templates.TemplateResponse(request, "auth/login.html", {"next": safe_next, "error": None})


@router.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form("/dashboard"),
    db: Session = Depends(get_db),
):
    # F-11 fix: rate-limit theo USERNAME (không phải IP) — máy standalone IP
    # luôn 127.0.0.1 nên IP-based vô tác dụng. 5 lần / 60s / mỗi username.
    if not check_login_rate(username):
        # 429 Too Many Requests — chỉ dội thông điệp ngắn, không leak username
        raise HTTPException(
            status_code=429,
            detail="Quá nhiều lần thử đăng nhập. Vui lòng đợi 1 phút rồi thử lại.",
        )

    user = auth_svc.authenticate(db, username, password)
    if not user:
        return templates.TemplateResponse(
            request, "auth/login.html",
            {"next": next, "error": "Tên đăng nhập hoặc mật khẩu không đúng, hoặc tài khoản bị khóa"},
            status_code=401,
        )

    # F-11: reset bộ đếm khi đăng nhập THÀNH CÔNG -> không phạt user thật
    # vì vài lần lỡ gõ sai trước đó.
    reset_login_rate(username)

    token = create_session_token(user["id"])
    # F-09: validate next lại lần nữa (defense-in-depth) — phòng case form
    # bị tamper hidden field next bằng JS console / Burp.
    safe_next = safe_next_url(next, default="/dashboard")
    redirect_url = "/auth/change-password" if user["must_change_password"] else safe_next
    response = RedirectResponse(redirect_url, status_code=302)
    # F-12 fix: dùng cờ USE_HTTPS riêng biệt thay vì suy diễn từ DEBUG.
    # - Production trên localhost (không TLS) -> USE_HTTPS=False -> cookie
    #   vẫn được trình duyệt gửi lại trên HTTP -> không bị "đăng nhập xong
    #   văng ngược ra trang login".
    # - Khi triển khai sau reverse proxy có TLS thật -> đặt USE_HTTPS=True.
    response.set_cookie(
        key=settings.SESSION_COOKIE,
        value=token,
        httponly=True,             # Chặn JS đọc cookie session (chống XSS đánh cắp phiên)
        samesite="lax",            # Chặn cross-site POST gửi kèm cookie (bổ trợ CSRF)
        secure=settings.USE_HTTPS, # F-12: chỉ True khi thật sự có HTTPS
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
