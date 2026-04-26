import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from backend.models.models import DoiTuong, LienHe, TaiChinh
import re

logger = logging.getLogger(__name__)


def search_profiles(
    db: Session,
    query: str = "",
    fields: Optional[str] = None,
    gioi_tinh: Optional[str] = None,
    dia_chi_xa: Optional[str] = None,
    nghe_nghiep: Optional[str] = None,
    page: int = 1,
    page_size: int = 25,
) -> Dict[str, Any]:
    stmt = select(DoiTuong).where(DoiTuong.is_draft == False)

    if query:
        # Split query by comma, semicolon or newline to support multiple inputs
        tokens = [t.strip() for t in re.split(r'[,;\n]+', query) if t.strip()]
        if not tokens:
            tokens = [query.strip()]

        from sqlalchemy import and_
        
        # Determine which fields to search
        search_all = not fields
        selected_fields = fields.split(',') if fields else []
        
        or_conditions = []
        
        if search_all or 'name' in selected_fields:
            or_conditions.append(DoiTuong.ho_ten.ilike(f"%{query}%"))
            
            # Accent-insensitive search via Python memory (fast enough for local DB)
            try:
                from backend.utils.fuzzy_matching import remove_vietnamese_diacritics
                query_normalized = remove_vietnamese_diacritics(query).lower()
                
                # Fetch all names
                all_names_query = select(DoiTuong.cccd, DoiTuong.ho_ten).where(DoiTuong.is_draft == False)
                all_names = db.execute(all_names_query).all()
                
                matched_cccds = []
                for cccd, name in all_names:
                    if name and query_normalized in remove_vietnamese_diacritics(name).lower():
                        matched_cccds.append(cccd)
                        
                if matched_cccds:
                    # chunk it to prevent SQLite "too many SQL variables" error (max 999)
                    if len(matched_cccds) > 900:
                        or_conditions.append(DoiTuong.cccd.in_(matched_cccds[:900]))
                    else:
                        or_conditions.append(DoiTuong.cccd.in_(matched_cccds))
            except ImportError:
                pass
            
        if search_all or 'cccd' in selected_fields:
            or_conditions.append(DoiTuong.cccd.in_(tokens))
            if len(tokens) == 1:
                or_conditions.append(DoiTuong.cccd.ilike(f"%{tokens[0]}%"))
                
        if search_all or 'phone' in selected_fields:
            or_conditions.append(
                select(LienHe.id).where(
                    and_(LienHe.cccd == DoiTuong.cccd, LienHe.gia_tri.in_(tokens))
                ).exists()
            )
            if len(tokens) == 1:
                or_conditions.append(
                    select(LienHe.id).where(
                        and_(LienHe.cccd == DoiTuong.cccd, LienHe.gia_tri.ilike(f"%{tokens[0]}%"))
                    ).exists()
                )
                
        # For backwards compatibility, if search_all is true or 'bank' is passed
        if search_all or 'bank' in selected_fields:
            or_conditions.append(
                select(TaiChinh.id).where(
                    and_(TaiChinh.cccd == DoiTuong.cccd, TaiChinh.so_tai_khoan.in_(tokens))
                ).exists()
            )
            if len(tokens) == 1:
                or_conditions.append(
                    select(TaiChinh.id).where(
                        and_(TaiChinh.cccd == DoiTuong.cccd, TaiChinh.so_tai_khoan.ilike(f"%{tokens[0]}%"))
                    ).exists()
                )

        if or_conditions:
            stmt = stmt.where(or_(*or_conditions))
    if gioi_tinh:
        stmt = stmt.where(DoiTuong.gioi_tinh == gioi_tinh)
    if dia_chi_xa:
        stmt = stmt.where(DoiTuong.dia_chi_xa == dia_chi_xa)
    if nghe_nghiep:
        stmt = stmt.where(DoiTuong.phan_loai_nghe_nghiep == nghe_nghiep)

    from sqlalchemy import func
    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(total_stmt).scalar_one()

    offset = (page - 1) * page_size
    rows = db.execute(stmt.order_by(DoiTuong.ho_ten).offset(offset).limit(page_size)).scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if total else 0,
        "results": [
            {
                "cccd": r.cccd,
                "ho_ten": r.ho_ten,
                "ngay_sinh": r.ngay_sinh.strftime("%d/%m/%Y") if r.ngay_sinh else "",
                "gioi_tinh": r.gioi_tinh or "",
                "dia_chi_xa": r.dia_chi_xa or "",
                "dia_chi_tinh": r.dia_chi_tinh or "",
                "nghe_nghiep": r.phan_loai_nghe_nghiep or "",
            }
            for r in rows
        ],
    }


def fuzzy_search(db: Session, ho_ten: str, threshold: int = 80) -> List[Dict]:
    try:
        from backend.utils.fuzzy_matching import find_similar_names
    except ImportError:
        return []

    all_rows = db.execute(
        select(DoiTuong.cccd, DoiTuong.ho_ten).where(
            DoiTuong.is_draft == False, DoiTuong.ho_ten.isnot(None)
        )
    ).all()

    cccd_list = [row[0] for row in all_rows]
    name_list = [row[1] for row in all_rows]
    raw_matches = find_similar_names(ho_ten, name_list, threshold=threshold)

    results = []
    for m in raw_matches:
        cccd = cccd_list[m["index"]]
        dt = db.get(DoiTuong, cccd)
        if dt:
            results.append({
                "cccd": dt.cccd,
                "ho_ten": dt.ho_ten,
                "ngay_sinh": dt.ngay_sinh.strftime("%d/%m/%Y") if dt.ngay_sinh else "",
                "dia_chi_xa": dt.dia_chi_xa or "",
                "score": m["score"],
            })
    return results
