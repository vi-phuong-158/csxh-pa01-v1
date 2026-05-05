# backend/routes/profile.py
"""
Routes liên quan tới hồ sơ đối tượng.

CÁC FIX BẢO MẬT ĐÃ ÁP DỤNG TRONG FILE NÀY:
    F-04 (Path Traversal qua CCCD): mọi handler nhận `cccd` từ URL đều
        validate ngay đầu hàm bằng `validate_cccd()` -> raise HTTP 400 nếu sai.
    F-05 (Bảo vệ thư mục Uploads): file lưu tại `data/uploads/...` (NGOÀI
        `frontend/static/`); response hiển thị qua URL `/api/documents/...`
        — yêu cầu xác thực, không public qua mount tĩnh.
    F-08 (Kiểm soát File Upload): mọi UploadFile chạy qua
        `validate_upload_file()` để giới hạn 5MB, MIME thật theo magic bytes,
        sanitize tên file gốc trước khi lưu DB.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from urllib.parse import quote

import aiofiles
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from backend.config import settings
from backend.constants import (
    LOAI_HINH_DAC_THU, LOAI_LIEN_HE, LOAI_QUAN_HE, LOAI_TAI_LIEU,
    LOAI_XE, NGAN_HANG, PHAN_LOAI_NGHE_NGHIEP, TINH_THANH, XA_PHUONG,
    DANH_SACH_QUOC_GIA, DAN_TOC, TON_GIAO,
)
from backend.db.session import get_db
from backend.deps import require_admin, require_login, require_profile_access
from backend.models.models import DoiTuong, TaiLieu
from backend.services import profile as profile_svc
from backend.services.docx_export import generate_profile_docx
from backend.utils.validators import (
    sanitize_filename, validate_cccd, validate_upload_file,
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
    "danh_sach_quoc_gia": DANH_SACH_QUOC_GIA,
    "dan_toc": DAN_TOC,
    "ton_giao": TON_GIAO,
}

# F-08: ngưỡng dung lượng tối đa cho 1 file upload (5 MB theo yêu cầu).
# Có thể nâng qua settings.MAX_UPLOAD_MB nhưng cap cứng 5MB ở route này.
_MAX_UPLOAD_BYTES = 5 * 1024 * 1024

# Allowlist MIME thật cho ảnh chân dung và tài liệu (DOC/PDF + ảnh).
_AVATAR_MIME = {"image/jpeg", "image/png", "image/webp"}
_DOC_MIME = {
    "image/jpeg", "image/png", "image/webp",
    "application/pdf",
    "application/msword",  # .doc cũ
    "application/zip",     # .docx (zip-based Office Open XML)
}


# ============================================================================
# F-04 helper — Dependency rút gọn để FastAPI tự gọi validate_cccd().
# ============================================================================
def _cccd_dep(cccd: str) -> str:
    """Dependency: validate `cccd` từ path. Raise 400 nếu sai chuẩn."""
    return validate_cccd(cccd)


# ============================================================================
# Export DOCX
# ============================================================================
@router.get("/{cccd}/export-docx")
def export_docx(
    cccd: str = Depends(_cccd_dep),
    user: dict = Depends(require_profile_access),
    db: Session = Depends(get_db),
):
    """Tải file DOCX báo cáo hồ sơ."""
    data = profile_svc.get_profile_full(db, cccd)
    if not data:
        return HTMLResponse("Không tìm thấy hồ sơ", status_code=404)
    docx_bytes = generate_profile_docx(data, base_dir=str(settings.BASE_DIR))
    if not docx_bytes:
        return HTMLResponse("Không thể tạo báo cáo", status_code=500)
    ho_ten = (data.get("ho_ten") or cccd).replace(" ", "_")
    filename = f"HoSo_{ho_ten}_{cccd}.docx"
    encoded = quote(filename, safe="")
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}"},
    )


# ============================================================================
# Trang chi tiết hồ sơ + load tab động (HTMX)
# ============================================================================
@router.get("/{cccd}", response_class=HTMLResponse)
def profile_page(
    request: Request,
    cccd: str = Depends(_cccd_dep),
    user: dict = Depends(require_profile_access),
    db: Session = Depends(get_db),
):
    data = profile_svc.get_profile_full(db, cccd)
    if not data:
        return HTMLResponse("Không tìm thấy hồ sơ", status_code=404)
    return templates.TemplateResponse(
        request, "profile/index.html",
        {"user": user, "profile": data, **_CTX_OPTS},
    )


@router.get("/{cccd}/tab/{tab_name}", response_class=HTMLResponse)
def profile_tab(
    tab_name: str,
    request: Request,
    cccd: str = Depends(_cccd_dep),
    user: dict = Depends(require_profile_access),
    db: Session = Depends(get_db),
):
    data = profile_svc.get_profile_full(db, cccd)
    if not data:
        return HTMLResponse("", status_code=404)
    template_map = {
        "nhan-than":     "profile/_tab_nhan_than.html",
        "lien-he":       "profile/_tab_lien_he.html",
        "tai-chinh":     "profile/_tab_tai_chinh.html",
        "phuong-tien":   "profile/_tab_phuong_tien.html",
        "ho-so-dac-thu": "profile/_tab_ho_so_dac_thu.html",
        "tai-lieu":      "profile/_tab_tai_lieu.html",
        "qua-trinh":     "profile/_tab_qua_trinh.html",
    }
    tpl = template_map.get(tab_name)
    if not tpl:
        return HTMLResponse("Tab không tồn tại", status_code=404)
    return templates.TemplateResponse(
        request, tpl, {"user": user, "profile": data, **_CTX_OPTS},
    )


def _tab_response(request, db, cccd, user, tpl):
    """Helper: nạp lại data hồ sơ và render partial của 1 tab."""
    data = profile_svc.get_profile_full(db, cccd)
    return templates.TemplateResponse(
        request, tpl, {"user": user, "profile": data, **_CTX_OPTS},
    )


# ============================================================================
# Cập nhật thông tin cơ bản
# ============================================================================
@router.post("/{cccd}/update")
async def update_basic(
    request: Request,
    cccd: str = Depends(_cccd_dep),
    user: dict = Depends(require_profile_access),
    db: Session = Depends(get_db),
):
    form = await request.form()
    data = dict(form)
    ok, msg = profile_svc.update_basic_info(db, cccd, data, user["username"])
    if request.headers.get("HX-Request"):
        cls = "text-green-400" if ok else "text-red-400"
        return HTMLResponse(f'<p class="{cls}">{msg}</p>')
    return RedirectResponse(f"/profile/{cccd}", status_code=302)


# ============================================================================
# CRUD nhân thân / liên hệ / tài chính / phương tiện / hồ sơ đặc thù / quá trình
# (DB-only, không động chạm filesystem — vẫn validate cccd defense-in-depth)
# ============================================================================
@router.post("/{cccd}/nhan-than")
async def add_nhan_than(
    request: Request,
    cccd: str = Depends(_cccd_dep),
    user: dict = Depends(require_profile_access),
    db: Session = Depends(get_db),
):
    profile_svc.add_nhan_than(db, cccd, dict(await request.form()))
    return _tab_response(request, db, cccd, user, "profile/_tab_nhan_than.html")


@router.delete("/{cccd}/nhan-than/{item_id}", response_class=HTMLResponse)
def delete_nhan_than(
    item_id: int,
    request: Request,
    cccd: str = Depends(_cccd_dep),
    user: dict = Depends(require_profile_access),
    db: Session = Depends(get_db),
):
    profile_svc.delete_nhan_than(db, item_id)
    return _tab_response(request, db, cccd, user, "profile/_tab_nhan_than.html")


@router.post("/{cccd}/lien-he")
async def add_lien_he(
    request: Request,
    cccd: str = Depends(_cccd_dep),
    user: dict = Depends(require_profile_access),
    db: Session = Depends(get_db),
):
    profile_svc.add_lien_he(db, cccd, dict(await request.form()))
    return _tab_response(request, db, cccd, user, "profile/_tab_lien_he.html")


@router.delete("/{cccd}/lien-he/{item_id}", response_class=HTMLResponse)
def delete_lien_he(
    item_id: int,
    request: Request,
    cccd: str = Depends(_cccd_dep),
    user: dict = Depends(require_profile_access),
    db: Session = Depends(get_db),
):
    profile_svc.delete_lien_he(db, item_id)
    return _tab_response(request, db, cccd, user, "profile/_tab_lien_he.html")


@router.post("/{cccd}/tai-chinh")
async def add_tai_chinh(
    request: Request,
    cccd: str = Depends(_cccd_dep),
    user: dict = Depends(require_profile_access),
    db: Session = Depends(get_db),
):
    profile_svc.add_tai_chinh(db, cccd, dict(await request.form()))
    return _tab_response(request, db, cccd, user, "profile/_tab_tai_chinh.html")


@router.delete("/{cccd}/tai-chinh/{item_id}", response_class=HTMLResponse)
def delete_tai_chinh(
    item_id: int,
    request: Request,
    cccd: str = Depends(_cccd_dep),
    user: dict = Depends(require_profile_access),
    db: Session = Depends(get_db),
):
    profile_svc.delete_tai_chinh(db, item_id)
    return _tab_response(request, db, cccd, user, "profile/_tab_tai_chinh.html")


@router.post("/{cccd}/phuong-tien")
async def add_phuong_tien(
    request: Request,
    cccd: str = Depends(_cccd_dep),
    user: dict = Depends(require_profile_access),
    db: Session = Depends(get_db),
):
    profile_svc.add_phuong_tien(db, cccd, dict(await request.form()))
    return _tab_response(request, db, cccd, user, "profile/_tab_phuong_tien.html")


@router.delete("/{cccd}/phuong-tien/{item_id}", response_class=HTMLResponse)
def delete_phuong_tien(
    item_id: int,
    request: Request,
    cccd: str = Depends(_cccd_dep),
    user: dict = Depends(require_profile_access),
    db: Session = Depends(get_db),
):
    profile_svc.delete_phuong_tien(db, item_id)
    return _tab_response(request, db, cccd, user, "profile/_tab_phuong_tien.html")


@router.post("/{cccd}/ho-so-dac-thu")
async def add_dac_thu(
    request: Request,
    cccd: str = Depends(_cccd_dep),
    user: dict = Depends(require_profile_access),
    db: Session = Depends(get_db),
):
    profile_svc.add_ho_so_dac_thu(db, cccd, dict(await request.form()))
    return _tab_response(request, db, cccd, user, "profile/_tab_ho_so_dac_thu.html")


@router.delete("/{cccd}/ho-so-dac-thu/{item_id}", response_class=HTMLResponse)
def delete_dac_thu(
    item_id: int,
    request: Request,
    cccd: str = Depends(_cccd_dep),
    user: dict = Depends(require_profile_access),
    db: Session = Depends(get_db),
):
    profile_svc.delete_ho_so_dac_thu(db, item_id)
    return _tab_response(request, db, cccd, user, "profile/_tab_ho_so_dac_thu.html")


@router.post("/{cccd}/qua-trinh")
async def add_qua_trinh(
    request: Request,
    cccd: str = Depends(_cccd_dep),
    user: dict = Depends(require_profile_access),
    db: Session = Depends(get_db),
):
    profile_svc.add_qua_trinh(db, cccd, dict(await request.form()))
    return _tab_response(request, db, cccd, user, "profile/_tab_qua_trinh.html")


@router.delete("/{cccd}/qua-trinh/{item_id}", response_class=HTMLResponse)
def delete_qua_trinh(
    item_id: int,
    request: Request,
    cccd: str = Depends(_cccd_dep),
    user: dict = Depends(require_profile_access),
    db: Session = Depends(get_db),
):
    profile_svc.delete_qua_trinh(db, item_id)
    return _tab_response(request, db, cccd, user, "profile/_tab_qua_trinh.html")


# ============================================================================
# F-05 + F-08: UPLOAD AVATAR & DOC — file lưu trong data/uploads/ (ngoài static)
# ============================================================================
@router.post("/{cccd}/upload-avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    cccd: str = Depends(_cccd_dep),
    user: dict = Depends(require_profile_access),
    db: Session = Depends(get_db),
):
    """
    Upload ảnh chân dung. Quy trình:
        1) F-04: cccd đã được validate qua _cccd_dep.
        2) F-08: validate_upload_file -> max 5MB + MIME thật khớp ảnh.
        3) F-05: lưu file vào `<UPLOAD_DIR>/avatars/<cccd>/<uuid>.<ext>`,
                ngoài thư mục static, chỉ truy cập được qua /api/documents/.
    """
    checked = await validate_upload_file(file, _AVATAR_MIME, _MAX_UPLOAD_BYTES)

    folder = (Path(settings.BASE_DIR) / settings.UPLOAD_DIR / "avatars" / cccd).resolve()
    folder.mkdir(parents=True, exist_ok=True)

    # Tên file LƯU TRÊN ĐĨA do server tự sinh — KHÔNG dùng tên client.
    stored_name = f"{uuid.uuid4().hex}{checked.extension}"
    dest = folder / stored_name
    async with aiofiles.open(dest, "wb") as f:
        await f.write(checked.content)

    # Đường dẫn LOGIC lưu DB (relative tới UPLOAD_DIR) — không kèm
    # prefix "/static/" vì file không nằm dưới static nữa.
    rel_path = f"avatars/{cccd}/{stored_name}"
    dt = db.get(DoiTuong, cccd)
    if dt:
        dt.anh_chan_dung = rel_path
        db.commit()

    # F-05: trả URL serve qua endpoint có auth
    serve_url = f"/api/documents/{rel_path}"
    return HTMLResponse(
        f'<img src="{serve_url}" class="w-24 h-24 rounded-full object-cover">'
    )


@router.post("/{cccd}/upload-doc")
async def upload_doc(
    request: Request,
    file: UploadFile = File(...),
    loai_tai_lieu: str = Form(""),
    mo_ta: str = Form(""),
    cccd: str = Depends(_cccd_dep),
    user: dict = Depends(require_profile_access),
    db: Session = Depends(get_db),
):
    """
    Upload tài liệu (PDF/DOC/DOCX/ảnh). Áp F-04 + F-05 + F-08 đầy đủ.
    Tên file gốc do client gửi -> sanitize TRƯỚC khi lưu DB và hiển thị,
    chống XSS qua attribute / text node của template Jinja.
    """
    checked = await validate_upload_file(file, _DOC_MIME, _MAX_UPLOAD_BYTES)

    folder = (Path(settings.BASE_DIR) / settings.UPLOAD_DIR / "docs" / cccd).resolve()
    folder.mkdir(parents=True, exist_ok=True)

    stored_name = f"{uuid.uuid4().hex}{checked.extension}"
    dest = folder / stored_name
    async with aiofiles.open(dest, "wb") as f:
        await f.write(checked.content)

    rel_path = f"docs/{cccd}/{stored_name}"

    # F-08: tên gốc của user -> sanitize. Lưu cả tên gốc (đã sạch) lẫn
    # tên server-side (UUID) để đối chiếu khi cần.
    safe_original = sanitize_filename(checked.safe_name)

    db.add(TaiLieu(
        cccd=cccd,
        ten_file_goc=safe_original,
        ten_file_luu=stored_name,
        duong_dan=rel_path,
        loai_tai_lieu=sanitize_filename(loai_tai_lieu, max_len=50),
        mo_ta=mo_ta[:1000] if mo_ta else "",
        dinh_dang=checked.extension.lstrip(".") or "bin",
    ))
    db.commit()

    return _tab_response(request, db, cccd, user, "profile/_tab_tai_lieu.html")


@router.delete("/{cccd}/tai-lieu/{item_id}", response_class=HTMLResponse)
def delete_tai_lieu(
    item_id: int,
    request: Request,
    cccd: str = Depends(_cccd_dep),
    user: dict = Depends(require_profile_access),
    db: Session = Depends(get_db),
):
    profile_svc.delete_tai_lieu(db, item_id)
    return _tab_response(request, db, cccd, user, "profile/_tab_tai_lieu.html")


# ============================================================================
# Xoá hồ sơ (admin only)
# ============================================================================
@router.delete("/{cccd}")
def delete_profile(
    cccd: str = Depends(_cccd_dep),
    user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Chỉ super_admin được xoá. cccd đã validate -> service an toàn rmtree."""
    ok, msg = profile_svc.delete_profile(db, cccd, user["username"])
    from fastapi import Response
    if ok:
        response = Response(status_code=204)
        response.headers["HX-Redirect"] = "/tra-cuu"
        return response
    import json
    return Response(
        status_code=204,
        headers={"HX-Trigger": json.dumps({"showToast": {"type": "error", "msg": msg}})}
    )
