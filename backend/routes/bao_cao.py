# File: backend/routes/bao_cao.py
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from backend.constants import PHAN_LOAI_NGHE_NGHIEP
from backend.db.session import get_db
from backend.deps import require_login
from backend.models.models import DoiTuong, LienHe, TaiChinh

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bao-cao", tags=["bao-cao"])
templates = Jinja2Templates(directory="frontend/templates")


@router.get("", response_class=HTMLResponse)
def bao_cao_page(request: Request, user: dict = Depends(require_login)):
    return templates.TemplateResponse(
        request,
        "bao_cao/index.html",
        {"user": user, "phan_loai_options": PHAN_LOAI_NGHE_NGHIEP},
    )


@router.get("/api/thong-ke")
def api_thong_ke(
    tu_ngay: Optional[str] = Query(None, description="YYYY-MM-DD"),
    den_ngay: Optional[str] = Query(None, description="YYYY-MM-DD"),
    phan_loai: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: dict = Depends(require_login),
):
    try:
        # --- Parse date range --------------------------------------------------
        dt_from: Optional[datetime] = None
        dt_to: Optional[datetime] = None
        if tu_ngay:
            dt_from = datetime.strptime(tu_ngay, "%Y-%m-%d")
        if den_ngay:
            dt_to = datetime.strptime(den_ngay, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59
            )

        # --- Shared filter factory ---------------------------------------------
        def base_filter():
            conds = [DoiTuong.is_draft == False]
            if dt_from:
                conds.append(DoiTuong.created_at >= dt_from)
            if dt_to:
                conds.append(DoiTuong.created_at <= dt_to)
            if phan_loai:
                conds.append(DoiTuong.phan_loai_nghe_nghiep == phan_loai)
            return and_(*conds)

        # --- Summary -----------------------------------------------------------
        total = db.execute(
            select(func.count(DoiTuong.cccd)).where(base_filter())
        ).scalar_one()

        draft_count = db.execute(
            select(func.count(DoiTuong.cccd)).where(DoiTuong.is_draft == True)
        ).scalar_one()

        co_sdt = db.execute(
            select(func.count(DoiTuong.cccd)).where(
                base_filter(),
                DoiTuong.cccd.in_(select(LienHe.cccd).distinct()),
            )
        ).scalar_one()

        co_stk = db.execute(
            select(func.count(DoiTuong.cccd)).where(
                base_filter(),
                DoiTuong.cccd.in_(select(TaiChinh.cccd).distinct()),
            )
        ).scalar_one()

        # --- By phan_loai_nghe_nghiep (Pie chart) ------------------------------
        phan_loai_rows = db.execute(
            select(DoiTuong.phan_loai_nghe_nghiep, func.count(DoiTuong.cccd))
            .where(base_filter())
            .group_by(DoiTuong.phan_loai_nghe_nghiep)
            .order_by(func.count(DoiTuong.cccd).desc())
        ).all()
        by_phan_loai = {(r[0] or "Không rõ"): r[1] for r in phan_loai_rows}

        # --- By month (Bar chart) — last 24 months w/ data ---------------------
        month_col = func.strftime("%Y-%m", DoiTuong.created_at)
        month_rows = db.execute(
            select(month_col.label("month"), func.count(DoiTuong.cccd).label("cnt"))
            .where(base_filter(), DoiTuong.created_at.isnot(None))
            .group_by(month_col)
            .order_by(month_col)
            .limit(24)
        ).all()
        by_month = [{"month": r[0], "count": r[1]} for r in month_rows if r[0]]

        # --- By gioi_tinh (supplementary) -------------------------------------
        gioi_tinh_rows = db.execute(
            select(DoiTuong.gioi_tinh, func.count(DoiTuong.cccd))
            .where(base_filter())
            .group_by(DoiTuong.gioi_tinh)
        ).all()
        by_gioi_tinh = {(r[0] or "Không rõ"): r[1] for r in gioi_tinh_rows}

        # --- By dia_ban top 10 ------------------------------------------------
        dia_ban_rows = db.execute(
            select(DoiTuong.dia_chi_xa, func.count(DoiTuong.cccd))
            .where(
                base_filter(),
                DoiTuong.dia_chi_xa.isnot(None),
                DoiTuong.dia_chi_xa != "",
            )
            .group_by(DoiTuong.dia_chi_xa)
            .order_by(func.count(DoiTuong.cccd).desc())
            .limit(10)
        ).all()
        by_dia_ban = {r[0]: r[1] for r in dia_ban_rows}

        # --- Detail table rows ------------------------------------------------
        table = [
            {
                "phan_loai": loai,
                "count": cnt,
                "pct": round(cnt / total * 100, 1) if total > 0 else 0,
            }
            for loai, cnt in by_phan_loai.items()
        ]

        return {
            "summary": {
                "total": total,
                "draft": draft_count,
                "co_sdt": co_sdt,
                "co_stk": co_stk,
            },
            "by_phan_loai": by_phan_loai,
            "by_month": by_month,
            "by_gioi_tinh": by_gioi_tinh,
            "by_dia_ban": by_dia_ban,
            "table": table,
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Lỗi api_thong_ke: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Lỗi thống kê: {exc}")
