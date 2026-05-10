# backend/main.py
"""
Entry point FastAPI cho VCFE Database.

Phase 3 thay đổi:
    - Đăng ký dependency global `csrf_protect` (F-10) -> mọi request
      POST/PUT/PATCH/DELETE bị kiểm tra CSRF token.
    - Middleware `csrf_cookie_middleware`: với mọi response trang HTML,
      đảm bảo client có cookie `csrf_token` (httponly=False) để JS HTMX
      đọc và gắn vào header X-CSRF-Token.
    - Bỏ CORS toàn cục `allow_origins=["*"]` — app offline same-origin,
      không cần CORS; lại còn bị spec không hợp lệ với credentials=True.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.config import settings
from backend.db.session import init_db
from backend.deps import csrf_protect
from backend.limiter import limiter
from backend.routes import (
    audit_log, auth, bao_cao, danh_ba, dashboard, events, files, network,
    nguon_du_lieu, nhap_excel, nhap_lieu, profile, quan_he, quan_ly_user,
    ra_soat, tra_cuu,
)
from backend.security import issue_csrf_token

logging.basicConfig(level=logging.INFO if settings.DEBUG else logging.WARNING)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Khởi tạo super admin nếu DB mới
    from backend.db.session import SessionLocal
    from backend.services.auth import init_super_admin
    db = SessionLocal()
    try:
        init_super_admin(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan,
    # F-10: enforce CSRF cho TOÀN BỘ ứng dụng. Mỗi request unsafe phải có
    # token hợp lệ; csrf_protect tự bỏ qua GET/HEAD/OPTIONS.
    dependencies=[Depends(csrf_protect)],
)

# (CORS đã được gỡ ở Phase 1 review — app offline same-origin)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ============================================================================
# F-10: Middleware đặt cookie csrf_token cho mọi GET trang HTML
# ============================================================================
@app.middleware("http")
async def csrf_cookie_middleware(request: Request, call_next):
    """
    Đảm bảo client luôn có cookie `csrf_token` (httponly=False để JS đọc).

    - Nếu request đã có cookie -> tái sử dụng giá trị, set lại request.state
      để template hiển thị (cần tránh sinh token mới mỗi lần làm vô hiệu
      tab khác).
    - Nếu chưa có -> sinh token mới, set vào request.state TRƯỚC khi gọi
      handler (để template render được), và set cookie SAU khi handler trả.
    """
    existing = request.cookies.get("csrf_token")
    if existing:
        request.state.csrf_token = existing
        new_token = None
    else:
        new_token = issue_csrf_token()
        request.state.csrf_token = new_token

    response = await call_next(request)

    if new_token is not None:
        # httponly=False để JS đọc được giá trị (HTMX cần)
        # samesite=Lax để chặn cross-site GET kèm cookie
        # secure=USE_HTTPS (F-12) để cookie chạy được trên HTTP localhost
        response.set_cookie(
            key="csrf_token",
            value=new_token,
            httponly=False,
            samesite="lax",
            secure=settings.USE_HTTPS,
            max_age=8 * 60 * 60,  # đồng bộ với CSRF_MAX_AGE
            path="/",
        )
    return response


# ============================================================================
# Static + Routes
# ============================================================================
# Static files — CHỈ phục vụ asset frontend công khai. Uploads serve qua
# /api/documents/... (xem F-05 fix).
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(tra_cuu.router)
app.include_router(ra_soat.router)
app.include_router(profile.router)
app.include_router(quan_he.router)
app.include_router(network.router)
app.include_router(nhap_lieu.router)
app.include_router(quan_ly_user.router)
app.include_router(audit_log.router)
app.include_router(nguon_du_lieu.router)
app.include_router(nhap_excel.router)
app.include_router(danh_ba.router)
app.include_router(bao_cao.router)
app.include_router(files.router)
app.include_router(events.router)


@app.get("/")
def root():
    return RedirectResponse("/dashboard", status_code=302)
