import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.config import settings
from backend.db.session import init_db
from backend.limiter import limiter
from backend.routes import auth, dashboard, tra_cuu, ra_soat, profile, nhap_lieu
from backend.routes import quan_ly_user, audit_log, nguon_du_lieu, nhap_excel
from backend.routes import danh_ba

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
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO Phase 8: thu hẹp về domain cụ thể khi production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Routes
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(tra_cuu.router)
app.include_router(ra_soat.router)
app.include_router(profile.router)
app.include_router(nhap_lieu.router)
app.include_router(quan_ly_user.router)
app.include_router(audit_log.router)
app.include_router(nguon_du_lieu.router)
app.include_router(nhap_excel.router)
app.include_router(danh_ba.router)


@app.get("/")
def root():
    return RedirectResponse("/dashboard", status_code=302)
