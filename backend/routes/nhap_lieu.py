from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.deps import require_login
from backend.services import profile as profile_svc
from backend.constants import (
    TINH_THANH, XA_PHUONG, LOAI_LIEN_HE, LOAI_QUAN_HE,
    LOAI_HINH_DAC_THU, NGAN_HANG, LOAI_XE, LOAI_TAI_LIEU,
    PHAN_LOAI_NGHE_NGHIEP, DANH_SACH_QUOC_GIA, DAN_TOC, TON_GIAO,
)

router = APIRouter(prefix="/nhap-lieu", tags=["nhap-lieu"])
templates = Jinja2Templates(directory="frontend/templates")

_CTX_OPTS = {
    "tinh_thanh": TINH_THANH,
    "xa_phuong": XA_PHUONG,
    "loai_lien_he": LOAI_LIEN_HE,
    "loai_quan_he": LOAI_QUAN_HE,
    "loai_hinh_dac_thu": LOAI_HINH_DAC_THU,
    "ngan_hang": NGAN_HANG,
    "loai_xe": LOAI_XE,
    "loai_tai_lieu": LOAI_TAI_LIEU,
    "phan_loai_nghe_nghiep": PHAN_LOAI_NGHE_NGHIEP,
    "danh_sach_quoc_gia": DANH_SACH_QUOC_GIA,
    "dan_toc": DAN_TOC,
    "ton_giao": TON_GIAO,
}


@router.get("", response_class=HTMLResponse)
def nhap_lieu_home(request: Request, user: dict = Depends(require_login)):
    return templates.TemplateResponse(request, "nhap_lieu/index.html", {"user": user, "cccd": None})


@router.post("/start")
async def start_draft(
    request: Request,
    user: dict = Depends(require_login),
    db: Session = Depends(get_db),
):
    form = await request.form()
    cccd = str(form.get("cccd", "")).strip()
    if not cccd or not cccd.isdigit() or len(cccd) not in (9, 12):
        return templates.TemplateResponse(
            request, "nhap_lieu/index.html",
            {"user": user, "cccd": None, "error": "CCCD không hợp lệ (9 hoặc 12 chữ số)"},
        )
    ok, msg = profile_svc.create_draft(db, cccd)
    if not ok:
        return templates.TemplateResponse(
            request, "nhap_lieu/index.html",
            {"user": user, "cccd": None, "error": msg},
        )
    return RedirectResponse(f"/nhap-lieu/{cccd}", status_code=302)


@router.get("/{cccd}", response_class=HTMLResponse)
def nhap_lieu_form(cccd: str, request: Request, user: dict = Depends(require_login), db: Session = Depends(get_db)):
    data = profile_svc.get_profile_full(db, cccd)
    if not data:
        return RedirectResponse("/nhap-lieu", status_code=302)
    return templates.TemplateResponse(request, "nhap_lieu/form.html", {
        "user": user, "profile": data, **_CTX_OPTS,
    })


@router.post("/{cccd}/save-basic")
async def save_basic(
    cccd: str, request: Request,
    user: dict = Depends(require_login),
    db: Session = Depends(get_db),
):
    form = await request.form()
    ok, msg = profile_svc.update_basic_info(db, cccd, dict(form), user["username"])
    if request.headers.get("HX-Request"):
        cls = "text-green-400" if ok else "text-red-400"
        return HTMLResponse(f'<p class="{cls} text-sm mt-1">{msg}</p>')
    return RedirectResponse(f"/nhap-lieu/{cccd}", status_code=302)


@router.post("/{cccd}/commit")
def commit(
    cccd: str,
    request: Request,
    user: dict = Depends(require_login),
    db: Session = Depends(get_db),
):
    ok, msg = profile_svc.commit_draft(db, cccd)
    if not ok:
        # Nếu lỗi, trả về trigger để hiện toast thông báo lỗi (dùng 204 để không swap đè nút)
        from fastapi import Response
        import json
        return Response(
            status_code=204,
            headers={"HX-Trigger": json.dumps({"showToast": {"type": "error", "msg": msg}})}
        )
    
    # Thành công: Điều hướng toàn trang bằng HX-Redirect
    from fastapi import Response
    response = Response(status_code=204)
    response.headers["HX-Redirect"] = f"/profile/{cccd}"
    return response


@router.delete("/{cccd}")
def cancel_draft(
    cccd: str,
    user: dict = Depends(require_login),
    db: Session = Depends(get_db),
):
    ok, msg = profile_svc.delete_profile(db, cccd, user["username"])
    if ok:
        from fastapi import Response
        response = Response(status_code=204)
        response.headers["HX-Redirect"] = "/nhap-lieu"
        return response
    return {"ok": ok, "message": msg}


@router.get("/api/autofill")
def autofill(cccd: str, user: dict = Depends(require_login), db: Session = Depends(get_db)):
    data = profile_svc.get_profile_full(db, cccd)
    if data and not data["is_draft"]:
        return {"found": True, "data": data}
    return {"found": False}
