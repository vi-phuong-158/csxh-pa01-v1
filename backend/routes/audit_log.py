from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import Optional

from backend.db.session import get_db
from backend.deps import require_admin
from backend.models.models import AuditLog

router = APIRouter(prefix="/audit-log", tags=["admin"])
templates = Jinja2Templates(directory="frontend/templates")


@router.get("", response_class=HTMLResponse)
def audit_log_page(
    request: Request,
    page: int = 1,
    page_size: int = 50,
    nguoi: Optional[str] = None,
    hanh_dong: Optional[str] = None,
    user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    stmt = select(AuditLog)
    if nguoi:
        stmt = stmt.where(AuditLog.nguoi_thuc_hien.ilike(f"%{nguoi}%"))
    if hanh_dong:
        stmt = stmt.where(AuditLog.hanh_dong == hanh_dong)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    offset = (page - 1) * page_size
    rows = db.execute(stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size)).scalars().all()

    return templates.TemplateResponse(request, "audit_log/index.html", {
        "user": user,
        "logs": rows, "total": total, "page": page,
        "page_size": page_size, "pages": (total + page_size - 1) // page_size if total else 0,
        "filter_nguoi": nguoi or "", "filter_hanh_dong": hanh_dong or "",
    })
