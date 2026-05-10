from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from backend.constants import (
    DANH_SACH_QUOC_GIA, DAN_TOC, LOAI_QUAN_HE_DEF,
    PHAN_LOAI_NGHE_NGHIEP, TINH_THANH, TON_GIAO, XA_PHUONG,
)
from backend.db.session import get_db
from backend.deps import require_login, require_profile_access
from backend.services import profile as profile_svc
from backend.services import quan_he as qh_svc
from backend.utils.validators import validate_cccd

router = APIRouter(prefix="/profile", tags=["quan-he"])
templates = Jinja2Templates(directory="frontend/templates")

_CTX_OPTS = {
    "tinh_thanh": TINH_THANH,
    "xa_phuong": XA_PHUONG,
    "dan_toc": DAN_TOC,
    "ton_giao": TON_GIAO,
    "danh_sach_quoc_gia": DANH_SACH_QUOC_GIA,
    "phan_loai_nghe_nghiep": PHAN_LOAI_NGHE_NGHIEP,
    "loai_quan_he_def": LOAI_QUAN_HE_DEF,
}


def _cccd_dep(cccd: str) -> str:
    return validate_cccd(cccd)


def _tab_response(request: Request, db: Session, cccd: str, user: dict):
    data = profile_svc.get_profile_full(db, cccd)
    return templates.TemplateResponse(
        request, "profile/_tab_quan_he.html",
        {"user": user, "profile": data, **_CTX_OPTS},
    )


def _toast(ok: bool, msg: str) -> dict:
    t = "success" if ok else "error"
    return {"HX-Trigger": json.dumps({"showToast": {"type": t, "msg": msg}})}


@router.post("/{cccd}/quan-he/graph")
async def add_graph(
    request: Request,
    cccd: str = Depends(_cccd_dep),
    user: dict = Depends(require_profile_access),
    db: Session = Depends(get_db),
):
    data = dict(await request.form())
    ok, msg = qh_svc.add_quan_he_co_cccd(db, cccd, data)
    resp = _tab_response(request, db, cccd, user)
    resp.headers.update(_toast(ok, msg))
    return resp


@router.post("/{cccd}/quan-he/satellite")
async def add_satellite(
    request: Request,
    cccd: str = Depends(_cccd_dep),
    user: dict = Depends(require_profile_access),
    db: Session = Depends(get_db),
):
    data = dict(await request.form())
    ok, msg = qh_svc.add_quan_he_khong_cccd(db, cccd, data)
    resp = _tab_response(request, db, cccd, user)
    resp.headers.update(_toast(ok, msg))
    return resp


@router.delete("/{cccd}/quan-he/graph/{edge_id}", response_class=HTMLResponse)
def delete_graph(
    edge_id: int,
    request: Request,
    cccd: str = Depends(_cccd_dep),
    user: dict = Depends(require_profile_access),
    db: Session = Depends(get_db),
):
    ok, msg = qh_svc.delete_quan_he_graph(db, cccd, edge_id)
    resp = _tab_response(request, db, cccd, user)
    resp.headers.update(_toast(ok, msg))
    return resp


@router.delete("/{cccd}/quan-he/satellite/{item_id}", response_class=HTMLResponse)
def delete_satellite(
    item_id: int,
    request: Request,
    cccd: str = Depends(_cccd_dep),
    user: dict = Depends(require_profile_access),
    db: Session = Depends(get_db),
):
    ok, msg = qh_svc.delete_quan_he_satellite(db, item_id)
    resp = _tab_response(request, db, cccd, user)
    resp.headers.update(_toast(ok, msg))
    return resp


@router.get("/{cccd}/quan-he/preview-cccd", response_class=HTMLResponse)
def preview_cccd_endpoint(
    request: Request,
    cccd: str = Depends(_cccd_dep),
    cccd_doi_tac: str = "",
    user: dict = Depends(require_login),
    db: Session = Depends(get_db),
):
    """HTMX banner: kiểm tra CCCD đối tác đã có hồ sơ chưa."""
    val = (cccd_doi_tac or "").strip()
    if not val or len(val) not in (9, 12):
        return HTMLResponse("")

    result = qh_svc.preview_cccd(db, val)
    if result["has_profile"]:
        ho_ten = result["ho_ten"] or "(Chưa có tên)"
        ns = f" — sinh {result['ngay_sinh']}" if result.get("ngay_sinh") else ""
        draft = ' <span class="badge badge-yellow text-xs ml-1">Nháp</span>' if result["is_draft"] else ""
        return HTMLResponse(
            f'<div class="mt-1 p-2 rounded bg-emerald-900/40 border border-emerald-500/40 text-xs text-emerald-300">'
            f'🟢 Đã có hồ sơ: <strong>{ho_ten}</strong>{ns}{draft}'
            f'<br><span class="text-slate-400">→ Sẽ liên kết tới hồ sơ này</span>'
            f'</div>'
        )
    return HTMLResponse(
        '<div class="mt-1 p-2 rounded bg-amber-900/40 border border-amber-500/40 text-xs text-amber-300">'
        '🟡 Chưa có hồ sơ — sẽ tạo mới khi lưu'
        '</div>'
    )
