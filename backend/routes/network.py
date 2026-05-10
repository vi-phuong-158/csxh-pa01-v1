from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.deps import require_login
from backend.models.models import DoiTuong
from backend.services import network as network_svc
from backend.utils.validators import validate_cccd

router = APIRouter(prefix="/network", tags=["network"])
templates = Jinja2Templates(directory="frontend/templates")


def _cccd_dep(cccd: str) -> str:
    return validate_cccd(cccd)


@router.get("/search")
def search_profiles(
    q: str = Query(default=""),
    user: dict = Depends(require_login),
    db: Session = Depends(get_db),
):
    """Tìm kiếm hồ sơ theo tên hoặc CCCD — dùng cho typeahead."""
    if len(q) < 2:
        return []
    rows = db.execute(
        select(DoiTuong.cccd, DoiTuong.ho_ten)
        .where(or_(DoiTuong.ho_ten.ilike(f"%{q}%"), DoiTuong.cccd.contains(q)))
        .limit(10)
    ).all()
    return [{"cccd": r.cccd, "ho_ten": r.ho_ten or f"[{r.cccd}]"} for r in rows]


@router.get("/profile/{cccd}/api")
def profile_network_api(
    cccd: str = Depends(_cccd_dep),
    depth: int = Query(default=2, ge=1, le=3),
    user: dict = Depends(require_login),
    db: Session = Depends(get_db),
):
    """JSON BFS từ 1 hồ sơ — dùng cho tab Mạng lưới."""
    return network_svc.get_network_bfs(db, cccd, depth)


@router.get("", response_class=HTMLResponse)
def network_page(
    request: Request,
    user: dict = Depends(require_login),
):
    """Trang mạng lưới toàn cục."""
    return templates.TemplateResponse(request, "network/index.html", {"user": user})


@router.get("/api/data")
def global_network_api(
    cccd: List[str] = Query(default=[]),
    depth: int = Query(default=2, ge=1, le=3),
    user: dict = Depends(require_login),
    db: Session = Depends(get_db),
):
    """JSON mạng lưới hợp nhất từ danh sách CCCD được chọn."""
    if not cccd:
        return {"nodes": [], "links": [], "categories": []}
    return network_svc.get_multi_bfs(db, cccd, depth)
