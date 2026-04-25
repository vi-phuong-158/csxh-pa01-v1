from fastapi import APIRouter, Depends, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.deps import require_login

router = APIRouter(prefix="/nhap-excel", tags=["nhap-excel"])
templates = Jinja2Templates(directory="frontend/templates")


@router.get("", response_class=HTMLResponse)
def nhap_excel_page(request: Request, user: dict = Depends(require_login)):
    return templates.TemplateResponse(request, "nhap_excel/index.html", {"user": user})


@router.get("/download-template")
def download_template(user: dict = Depends(require_login)):
    """Tải file mẫu Excel chuẩn."""
    from fastapi.responses import FileResponse
    from pathlib import Path
    from backend.config import settings
    template_path = Path(settings.BASE_DIR) / "mau_ho_so_csxh.xlsx"
    if not template_path.exists():
        from fastapi.responses import HTMLResponse
        return HTMLResponse("File mẫu chưa có trên máy chủ", status_code=404)
    return FileResponse(
        path=str(template_path),
        filename="mau_ho_so_csxh.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


import pandas as pd
import io
from datetime import datetime
from backend.models.models import DoiTuong

@router.post("/upload")
async def upload_excel(
    request: Request,
    file: UploadFile = File(...),
    user: dict = Depends(require_login),
    db: Session = Depends(get_db),
):
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        required_cols = ['cccd', 'ho_ten']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            return templates.TemplateResponse(request, "nhap_excel/_results.html", {
                "error": f"File Excel thiếu các cột bắt buộc: {', '.join(missing)}"
            })
            
        success_count = 0
        failed_count = 0
        errors = []
        
        for idx, row in df.iterrows():
            row_num = idx + 2
            cccd = str(row.get('cccd', '')).strip()
            ho_ten = str(row.get('ho_ten', '')).strip()
            
            if not cccd or cccd == 'nan' or not ho_ten or ho_ten == 'nan':
                failed_count += 1
                errors.append({"row": row_num, "msg": "CCCD hoặc Họ tên bị trống"})
                continue
                
            # Check if CCCD exists
            existing = db.get(DoiTuong, cccd)
            if existing:
                failed_count += 1
                errors.append({"row": row_num, "msg": f"CCCD {cccd} đã tồn tại trong hệ thống"})
                continue
                
            # Parse date if available
            ngay_sinh = None
            ns_raw = row.get('ngay_sinh')
            if pd.notna(ns_raw):
                if isinstance(ns_raw, datetime):
                    ngay_sinh = ns_raw.date()
                else:
                    try:
                        ngay_sinh = pd.to_datetime(ns_raw).date()
                    except:
                        pass
                        
            dt = DoiTuong(
                cccd=cccd,
                ho_ten=ho_ten,
                ngay_sinh=ngay_sinh,
                gioi_tinh=str(row.get('gioi_tinh', '')) if pd.notna(row.get('gioi_tinh')) else None,
                dia_chi_tinh=str(row.get('dia_chi_tinh', '')) if pd.notna(row.get('dia_chi_tinh')) else None,
                dia_chi_xa=str(row.get('dia_chi_xa', '')) if pd.notna(row.get('dia_chi_xa')) else None,
                phan_loai_nghe_nghiep=str(row.get('phan_loai_nghe_nghiep', '')) if pd.notna(row.get('phan_loai_nghe_nghiep')) else None,
                chi_tiet_nghe_nghiep=str(row.get('chi_tiet_nghe_nghiep', '')) if pd.notna(row.get('chi_tiet_nghe_nghiep')) else None,
                ghi_chu_chung=str(row.get('ghi_chu_chung', '')) if pd.notna(row.get('ghi_chu_chung')) else None,
                is_draft=False
            )
            db.add(dt)
            success_count += 1
            
        db.commit()
        
        return templates.TemplateResponse(request, "nhap_excel/_results.html", {
            "success": success_count,
            "failed": failed_count,
            "errors": errors
        })
        
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(request, "nhap_excel/_results.html", {
            "error": f"Lỗi xử lý file: {str(e)}"
        })
