from fastapi import APIRouter, Depends, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.deps import require_login

router = APIRouter(prefix="/ra-soat", tags=["ra-soat"])
templates = Jinja2Templates(directory="frontend/templates")


@router.get("", response_class=HTMLResponse)
def ra_soat_page(request: Request, user: dict = Depends(require_login)):
    return templates.TemplateResponse(request, "ra_soat/index.html", {"user": user})


import pandas as pd
import io
from sqlalchemy import select
from backend.models.models import DoiTuong
from backend.utils.fuzzy_matching import batch_screen

@router.post("/api/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    user: dict = Depends(require_login),
    db: Session = Depends(get_db),
):
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # Check if ho_ten column exists
        if 'ho_ten' not in df.columns:
            return templates.TemplateResponse(request, "ra_soat/_results.html", {
                "error": "File Excel không có cột 'ho_ten'. Vui lòng kiểm tra lại."
            })
            
        input_names = df['ho_ten'].dropna().astype(str).tolist()
        
        # Get all names from DB
        db_names = db.execute(
            select(DoiTuong.ho_ten).where(DoiTuong.is_draft == False)
        ).scalars().all()
        db_names = [n for n in db_names if n]
        
        # Perform batch screening
        results = batch_screen(input_names, db_names)
        
        return templates.TemplateResponse(request, "ra_soat/_results.html", {
            "results": results
        })
        
    except Exception as e:
        return templates.TemplateResponse(request, "ra_soat/_results.html", {
            "error": f"Lỗi xử lý file: {str(e)}"
        })
