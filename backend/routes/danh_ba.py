# File: backend/routes/danh_ba.py
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.deps import require_login
from backend.models.models import DoiTuong, LienHe, TaiChinh

router = APIRouter(prefix="/danh-ba", tags=["danh-ba"])
templates = Jinja2Templates(directory="frontend/templates")


@router.get("", response_class=HTMLResponse)
def danh_ba_page(request: Request, user: dict = Depends(require_login)):
    return templates.TemplateResponse(request, "danh_ba/index.html", {"user": user})


@router.get("/search", response_class=HTMLResponse)
def danh_ba_search(
    request: Request,
    query: str = Query(""),
    type: str = Query("phone"),
    user: dict = Depends(require_login),
    db: Session = Depends(get_db),
):
    q = query.strip()
    results = []

    if q:
        if type == "bank":
            rows = (
                db.query(TaiChinh, DoiTuong)
                .join(DoiTuong, TaiChinh.cccd == DoiTuong.cccd)
                .filter(
                    DoiTuong.is_draft == False,
                    TaiChinh.so_tai_khoan.ilike(f"%{q}%"),
                )
                .order_by(TaiChinh.so_tai_khoan)
                .limit(100)
                .all()
            )
            for tc, dt in rows:
                results.append({
                    "value": tc.so_tai_khoan or "",
                    "sub": tc.ngan_hang or "",
                    "chu": tc.chu_tai_khoan or "",
                    "ho_ten": dt.ho_ten or "",
                    "cccd": dt.cccd,
                    "ghi_chu": tc.ghi_chu or "",
                })
        else:
            rows = (
                db.query(LienHe, DoiTuong)
                .join(DoiTuong, LienHe.cccd == DoiTuong.cccd)
                .filter(
                    DoiTuong.is_draft == False,
                    LienHe.gia_tri.ilike(f"%{q}%"),
                )
                .order_by(LienHe.gia_tri)
                .limit(100)
                .all()
            )
            for lh, dt in rows:
                results.append({
                    "value": lh.gia_tri or "",
                    "sub": lh.loai_lien_he or "",
                    "chu": "",
                    "ho_ten": dt.ho_ten or "",
                    "cccd": dt.cccd,
                    "ghi_chu": lh.ghi_chu or "",
                })

    return templates.TemplateResponse(
        request,
        "_partials/danh_ba_results.html",
        {"results": results, "search_type": type, "query": q},
    )
