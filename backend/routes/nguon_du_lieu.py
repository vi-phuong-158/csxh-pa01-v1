from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.db.session import get_db
from backend.deps import require_admin
from backend.models.models import NguonDuLieu

router = APIRouter(prefix="/nguon-du-lieu", tags=["admin"])
templates = Jinja2Templates(directory="frontend/templates")


@router.get("", response_class=HTMLResponse)
def list_sources(request: Request, user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    sources = db.execute(select(NguonDuLieu).order_by(NguonDuLieu.thoi_gian_import.desc())).scalars().all()
    return templates.TemplateResponse(request, "nguon_du_lieu/index.html", {"user": user, "sources": sources})
