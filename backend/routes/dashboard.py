from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.deps import require_login
from backend.services import dashboard as dash_svc

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
templates = Jinja2Templates(directory="frontend/templates")


@router.get("", response_class=HTMLResponse)
def dashboard_page(request: Request, user: dict = Depends(require_login), db: Session = Depends(get_db)):
    stats = dash_svc.get_statistics(db)
    recent = dash_svc.get_recent_records(db)
    return templates.TemplateResponse(request, "dashboard/index.html", {
        "user": user,
        "stats": stats,
        "recent": recent,
    })


@router.get("/api/stats")
def api_stats(user: dict = Depends(require_login), db: Session = Depends(get_db)):
    return dash_svc.get_statistics(db)
