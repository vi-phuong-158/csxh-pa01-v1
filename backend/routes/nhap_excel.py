import logging

from fastapi import APIRouter, Depends, Request, UploadFile, File
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from backend.config import settings
from backend.db.session import get_db
from backend.deps import require_login
from backend.services.nhap_excel import build_template, import_workbook

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nhap-excel", tags=["nhap-excel"])
templates = Jinja2Templates(directory="frontend/templates")


@router.get("", response_class=HTMLResponse)
def nhap_excel_page(request: Request, user: dict = Depends(require_login)):
    return templates.TemplateResponse(request, "nhap_excel/index.html", {"user": user})


@router.get("/download-template")
def download_template(user: dict = Depends(require_login)):
    """File mẫu sinh động từ SHEET_DEFS — luôn khớp với importer,
    không lệch version như file tĩnh trước đây."""
    return Response(
        content=build_template(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="mau_ho_so_csxh.xlsx"'},
    )


@router.post("/upload")
def upload_excel(
    request: Request,
    file: UploadFile = File(...),
    user: dict = Depends(require_login),
    db: Session = Depends(get_db),
):
    # Route `def` thường: FastAPI tự chạy trong threadpool, pandas + DB không
    # block event loop của Uvicorn.
    try:
        # Chặn DoS bằng file lớn: đọc tối đa max_bytes + 1, thấy dư là vượt ngưỡng.
        max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
        contents = file.file.read(max_bytes + 1)
        if len(contents) > max_bytes:
            return templates.TemplateResponse(request, "nhap_excel/_results.html", {
                "error": f"File vượt quá kích thước cho phép ({settings.MAX_UPLOAD_MB}MB)"
            })

        report = import_workbook(db, contents, user.get("username"), file.filename)
        return templates.TemplateResponse(request, "nhap_excel/_results.html", report)

    except Exception as e:
        db.rollback()
        logger.exception("Lỗi xử lý file Excel import")
        return templates.TemplateResponse(request, "nhap_excel/_results.html", {
            "error": "Không xử lý được file. Kiểm tra lại đúng định dạng file mẫu; "
                     "nếu vẫn lỗi, liên hệ quản trị (chi tiết đã ghi trong log hệ thống)."
        })
