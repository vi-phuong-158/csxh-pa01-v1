from fastapi import APIRouter, Depends, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path
import aiofiles
import uuid

from backend.config import settings
from backend.db.session import get_db
from backend.deps import require_login, require_admin
from backend.services import profile as profile_svc
from backend.services.docx_export import generate_profile_docx
from backend.models.models import DoiTuong
from backend.constants import (
    TINH_THANH, XA_PHUONG, LOAI_LIEN_HE, LOAI_QUAN_HE,
    LOAI_HINH_DAC_THU, NGAN_HANG, LOAI_XE, LOAI_TAI_LIEU,
    PHAN_LOAI_NGHE_NGHIEP,
)

router = APIRouter(prefix="/profile", tags=["profile"])
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
}


@router.get("/{cccd}/export-docx")
def export_docx(cccd: str, user: dict = Depends(require_login), db: Session = Depends(get_db)):
    """Download a DOCX report for this profile."""
    from urllib.parse import quote
    data = profile_svc.get_profile_full(db, cccd)
    if not data:
        return HTMLResponse("Không tìm thấy hồ sơ", status_code=404)
    docx_bytes = generate_profile_docx(data, base_dir=str(settings.BASE_DIR))
    if not docx_bytes:
        return HTMLResponse("Không thể tạo báo cáo", status_code=500)
    ho_ten = (data.get("ho_ten") or cccd).replace(" ", "_")
    filename = f"HoSo_{ho_ten}_{cccd}.docx"
    # RFC 5987: encode UTF-8 filename so Vietnamese chars work in browsers
    encoded_filename = quote(filename, safe="")
    content_disposition = f"attachment; filename*=UTF-8''{encoded_filename}"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": content_disposition},
    )


@router.get("/{cccd}", response_class=HTMLResponse)
def profile_page(cccd: str, request: Request, user: dict = Depends(require_login), db: Session = Depends(get_db)):
    data = profile_svc.get_profile_full(db, cccd)
    if not data:
        return HTMLResponse("Không tìm thấy hồ sơ", status_code=404)
    return templates.TemplateResponse(request, "profile/index.html", {
        "user": user, "profile": data, **_CTX_OPTS,
    })


@router.get("/{cccd}/tab/{tab_name}", response_class=HTMLResponse)
def profile_tab(cccd: str, tab_name: str, request: Request, user: dict = Depends(require_login), db: Session = Depends(get_db)):
    data = profile_svc.get_profile_full(db, cccd)
    if not data:
        return HTMLResponse("", status_code=404)
    template_map = {
        "nhan-than":    "profile/_tab_nhan_than.html",
        "lien-he":      "profile/_tab_lien_he.html",
        "tai-chinh":    "profile/_tab_tai_chinh.html",
        "phuong-tien":  "profile/_tab_phuong_tien.html",
        "ho-so-dac-thu":"profile/_tab_ho_so_dac_thu.html",
        "tai-lieu":     "profile/_tab_tai_lieu.html",
        "qua-trinh":    "profile/_tab_qua_trinh.html",
    }
    tpl = template_map.get(tab_name)
    if not tpl:
        return HTMLResponse("Tab không tồn tại", status_code=404)
    return templates.TemplateResponse(request, tpl, {"user": user, "profile": data, **_CTX_OPTS})


def _tab_response(request, db, cccd, user, tpl):
    """Helper to reload profile data and render a tab partial."""
    data = profile_svc.get_profile_full(db, cccd)
    return templates.TemplateResponse(request, tpl, {"user": user, "profile": data, **_CTX_OPTS})


@router.post("/{cccd}/update")
async def update_basic(
    cccd: str, request: Request,
    user: dict = Depends(require_login),
    db: Session = Depends(get_db),
):
    form = await request.form()
    data = dict(form)
    ok, msg = profile_svc.update_basic_info(db, cccd, data, user["username"])
    if request.headers.get("HX-Request"):
        cls = "text-green-400" if ok else "text-red-400"
        return HTMLResponse(f'<p class="{cls}">{msg}</p>')
    return RedirectResponse(f"/profile/{cccd}", status_code=302)


@router.post("/{cccd}/nhan-than")
async def add_nhan_than(cccd: str, request: Request, user: dict = Depends(require_login), db: Session = Depends(get_db)):
    form = await request.form()
    profile_svc.add_nhan_than(db, cccd, dict(form))
    return _tab_response(request, db, cccd, user, "profile/_tab_nhan_than.html")


@router.delete("/{cccd}/nhan-than/{item_id}", response_class=HTMLResponse)
def delete_nhan_than(cccd: str, item_id: int, request: Request, user: dict = Depends(require_login), db: Session = Depends(get_db)):
    profile_svc.delete_nhan_than(db, item_id)
    return _tab_response(request, db, cccd, user, "profile/_tab_nhan_than.html")


@router.post("/{cccd}/lien-he")
async def add_lien_he(cccd: str, request: Request, user: dict = Depends(require_login), db: Session = Depends(get_db)):
    form = await request.form()
    profile_svc.add_lien_he(db, cccd, dict(form))
    return _tab_response(request, db, cccd, user, "profile/_tab_lien_he.html")


@router.delete("/{cccd}/lien-he/{item_id}", response_class=HTMLResponse)
def delete_lien_he(cccd: str, item_id: int, request: Request, user: dict = Depends(require_login), db: Session = Depends(get_db)):
    profile_svc.delete_lien_he(db, item_id)
    return _tab_response(request, db, cccd, user, "profile/_tab_lien_he.html")


@router.post("/{cccd}/tai-chinh")
async def add_tai_chinh(cccd: str, request: Request, user: dict = Depends(require_login), db: Session = Depends(get_db)):
    form = await request.form()
    profile_svc.add_tai_chinh(db, cccd, dict(form))
    return _tab_response(request, db, cccd, user, "profile/_tab_tai_chinh.html")


@router.delete("/{cccd}/tai-chinh/{item_id}", response_class=HTMLResponse)
def delete_tai_chinh(cccd: str, item_id: int, request: Request, user: dict = Depends(require_login), db: Session = Depends(get_db)):
    profile_svc.delete_tai_chinh(db, item_id)
    return _tab_response(request, db, cccd, user, "profile/_tab_tai_chinh.html")


@router.post("/{cccd}/phuong-tien")
async def add_phuong_tien(cccd: str, request: Request, user: dict = Depends(require_login), db: Session = Depends(get_db)):
    form = await request.form()
    profile_svc.add_phuong_tien(db, cccd, dict(form))
    return _tab_response(request, db, cccd, user, "profile/_tab_phuong_tien.html")


@router.delete("/{cccd}/phuong-tien/{item_id}", response_class=HTMLResponse)
def delete_phuong_tien(cccd: str, item_id: int, request: Request, user: dict = Depends(require_login), db: Session = Depends(get_db)):
    profile_svc.delete_phuong_tien(db, item_id)
    return _tab_response(request, db, cccd, user, "profile/_tab_phuong_tien.html")


@router.post("/{cccd}/ho-so-dac-thu")
async def add_dac_thu(cccd: str, request: Request, user: dict = Depends(require_login), db: Session = Depends(get_db)):
    form = await request.form()
    profile_svc.add_ho_so_dac_thu(db, cccd, dict(form))
    return _tab_response(request, db, cccd, user, "profile/_tab_ho_so_dac_thu.html")


@router.delete("/{cccd}/ho-so-dac-thu/{item_id}", response_class=HTMLResponse)
def delete_dac_thu(cccd: str, item_id: int, request: Request, user: dict = Depends(require_login), db: Session = Depends(get_db)):
    profile_svc.delete_ho_so_dac_thu(db, item_id)
    return _tab_response(request, db, cccd, user, "profile/_tab_ho_so_dac_thu.html")


@router.post("/{cccd}/qua-trinh")
async def add_qua_trinh(cccd: str, request: Request, user: dict = Depends(require_login), db: Session = Depends(get_db)):
    form = await request.form()
    profile_svc.add_qua_trinh(db, cccd, dict(form))
    return _tab_response(request, db, cccd, user, "profile/_tab_qua_trinh.html")


@router.delete("/{cccd}/qua-trinh/{item_id}", response_class=HTMLResponse)
def delete_qua_trinh(cccd: str, item_id: int, request: Request, user: dict = Depends(require_login), db: Session = Depends(get_db)):
    profile_svc.delete_qua_trinh(db, item_id)
    return _tab_response(request, db, cccd, user, "profile/_tab_qua_trinh.html")


@router.post("/{cccd}/upload-avatar")
async def upload_avatar(
    cccd: str,
    file: UploadFile = File(...),
    user: dict = Depends(require_login),
    db: Session = Depends(get_db),
):
    ALLOWED = {".jpg", ".jpeg", ".png", ".webp"}
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED:
        return HTMLResponse('<p class="text-red-400">Chỉ hỗ trợ JPG/PNG/WebP</p>', status_code=400)

    folder = Path(settings.BASE_DIR) / settings.UPLOAD_DIR / "avatars" / cccd
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = folder / filename

    async with aiofiles.open(dest, "wb") as f:
        await f.write(await file.read())

    rel_path = f"uploads/avatars/{cccd}/{filename}"
    dt = db.get(DoiTuong, cccd)
    if dt:
        dt.anh_chan_dung = rel_path
        db.commit()

    return HTMLResponse(f'<img src="/static/{rel_path}" class="w-24 h-24 rounded-full object-cover">')


@router.post("/{cccd}/upload-doc")
async def upload_doc(
    cccd: str,
    request: Request,
    file: UploadFile = File(...),
    loai_tai_lieu: str = Form(""),
    mo_ta: str = Form(""),
    user: dict = Depends(require_login),
    db: Session = Depends(get_db),
):
    ALLOWED = {".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png"}
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED:
        return HTMLResponse('<p class="text-red-400">File không hợp lệ</p>', status_code=400)

    folder = Path(settings.BASE_DIR) / settings.UPLOAD_DIR / "docs" / cccd
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = folder / filename

    async with aiofiles.open(dest, "wb") as f:
        await f.write(await file.read())

    rel_path = f"uploads/docs/{cccd}/{filename}"
    
    from backend.models.models import TaiLieu
    tl = TaiLieu(
        cccd=cccd,
        ten_file_goc=file.filename,
        ten_file_luu=filename,
        duong_dan=rel_path,
        loai_tai_lieu=loai_tai_lieu,
        mo_ta=mo_ta,
        dinh_dang=ext.strip(".")
    )
    db.add(tl)
    db.commit()

    return _tab_response(request, db, cccd, user, "profile/_tab_tai_lieu.html")


@router.delete("/{cccd}/tai-lieu/{item_id}", response_class=HTMLResponse)
def delete_tai_lieu(
    cccd: str, 
    item_id: int, 
    request: Request, 
    user: dict = Depends(require_login), 
    db: Session = Depends(get_db)
):
    profile_svc.delete_tai_lieu(db, item_id)
    return _tab_response(request, db, cccd, user, "profile/_tab_tai_lieu.html")



@router.delete("/{cccd}")
def delete_profile(
    cccd: str,
    user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    ok, msg = profile_svc.delete_profile(db, cccd, user["username"])
    return {"ok": ok, "message": msg}
