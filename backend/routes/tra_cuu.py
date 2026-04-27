from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from backend.db.session import get_db
from backend.deps import require_login
from backend.services import search as search_svc

router = APIRouter(prefix="/tra-cuu", tags=["tra-cuu"])
templates = Jinja2Templates(directory="frontend/templates")


@router.get("", response_class=HTMLResponse)
def tra_cuu_page(request: Request, user: dict = Depends(require_login)):
    return templates.TemplateResponse(request, "tra_cuu/index.html", {"user": user})


@router.get("/api/search")
def search(
    q: str = Query(""),
    fields: Optional[str] = None,
    gioi_tinh: Optional[str] = None,
    dia_chi_xa: Optional[str] = None,
    nghe_nghiep: Optional[str] = None,
    page: int = 1,
    page_size: int = 25,
    user: dict = Depends(require_login),
    db: Session = Depends(get_db),
):
    return search_svc.search_profiles(db, q, fields, gioi_tinh, dia_chi_xa, nghe_nghiep, page, page_size)


@router.get("/api/fuzzy")
def fuzzy(
    q: str = Query(""),
    threshold: int = 80,
    user: dict = Depends(require_login),
    db: Session = Depends(get_db),
):
    return search_svc.fuzzy_search(db, q, threshold)
