import logging

from fastapi import APIRouter, Depends, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.deps import require_login

logger = logging.getLogger(__name__)

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
import re
from datetime import datetime
from sqlalchemy import select
from backend.config import settings
from backend.models.models import DoiTuong, AuditLog

# CCCD mẫu mới 12 số / CMND cũ 9 số — đồng bộ với backend/utils/validators.py
_CCCD_RE = re.compile(r"^(?:\d{9}|\d{12})$")

# Database Safety (CLAUDE.md): commit theo chunk để tránh transaction khổng lồ
# giữ write-lock lâu trên SQLCipher gây "database is locked".
_CHUNK_SIZE = 100

# SQLite giới hạn ~999 biến bind / câu lệnh — chia nhỏ mệnh đề IN khi check trùng.
_IN_CLAUSE_SIZE = 500


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

        # Check trùng theo BATCH: 1 lượt query IN(...) cho toàn bộ file thay vì
        # db.get() từng dòng (N+1 — mỗi lượt là 1 connection mới với NullPool).
        all_cccd = [
            c for c in (str(v).strip() for v in df['cccd'].tolist())
            if _CCCD_RE.fullmatch(c)
        ]
        existing_cccd: set[str] = set()
        for i in range(0, len(all_cccd), _IN_CLAUSE_SIZE):
            batch = all_cccd[i:i + _IN_CLAUSE_SIZE]
            rows = db.execute(select(DoiTuong.cccd).where(DoiTuong.cccd.in_(batch))).all()
            existing_cccd.update(r[0] for r in rows)
        seen_in_file: set[str] = set()

        pending = 0  # số dòng đã add chưa commit trong chunk hiện tại

        for idx, row in df.iterrows():
            row_num = idx + 2
            cccd = str(row.get('cccd', '')).strip()
            ho_ten = str(row.get('ho_ten', '')).strip()

            if not cccd or cccd == 'nan' or not ho_ten or ho_ten == 'nan':
                failed_count += 1
                errors.append({"row": row_num, "msg": "CCCD hoặc Họ tên bị trống"})
                continue

            if not _CCCD_RE.fullmatch(cccd):
                failed_count += 1
                errors.append({"row": row_num, "msg": "CCCD không hợp lệ (phải đúng 9 hoặc 12 chữ số)"})
                continue

            if cccd in seen_in_file:
                failed_count += 1
                errors.append({"row": row_num, "msg": f"CCCD {cccd} bị lặp trong chính file Excel"})
                continue

            if cccd in existing_cccd:
                failed_count += 1
                errors.append({"row": row_num, "msg": f"CCCD {cccd} đã tồn tại trong hệ thống"})
                continue
            seen_in_file.add(cccd)
                
            # Parse date if available
            ngay_sinh = None
            ns_raw = row.get('ngay_sinh')
            if pd.notna(ns_raw):
                if isinstance(ns_raw, datetime):
                    ngay_sinh = ns_raw.date()
                else:
                    # F-15 fix: bắt CHÍNH XÁC ngoại lệ parse date thay vì
                    # bare `except:` (sẽ nuốt cả KeyboardInterrupt/SystemExit
                    # và ẩn lỗi nghiêm trọng). Khi gặp dữ liệu xấu, ghi log
                    # đầy đủ + đánh dấu dòng lỗi cho cán bộ rà soát Excel.
                    try:
                        ngay_sinh = pd.to_datetime(ns_raw).date()
                    except (ValueError, TypeError, pd.errors.ParserError) as e:
                        logger.warning(
                            "Excel row %s: không parse được ngay_sinh=%r: %s",
                            row_num, ns_raw, e,
                        )
                        errors.append({
                            "row": row_num,
                            "msg": f"Ngày sinh không hợp lệ ({ns_raw!r})",
                        })
                        
            dt = DoiTuong(
                cccd=cccd,
                ho_ten=ho_ten.upper(),
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
            pending += 1
            if pending >= _CHUNK_SIZE:
                db.commit()
                pending = 0

        db.commit()

        # Audit log: import hàng loạt là thao tác nhạy cảm, phải trace được
        # ai import file nào, bao nhiêu dòng vào/lỗi.
        try:
            db.add(AuditLog(
                bang="doi_tuong",
                hanh_dong="BULK_IMPORT",
                khoa_chinh=file.filename or "excel",
                du_lieu_moi=f"Import Excel: {success_count} thành công, {failed_count} lỗi",
                nguoi_thuc_hien=user.get("username"),
            ))
            db.commit()
        except Exception:
            logger.exception("Không thể ghi audit log BULK_IMPORT")

        return templates.TemplateResponse(request, "nhap_excel/_results.html", {
            "success": success_count,
            "failed": failed_count,
            "errors": errors
        })

    except Exception as e:
        db.rollback()
        logger.exception("Lỗi xử lý file Excel import")
        return templates.TemplateResponse(request, "nhap_excel/_results.html", {
            "error": f"Lỗi xử lý file: {str(e)}"
        })
