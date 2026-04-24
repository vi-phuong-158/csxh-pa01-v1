import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from backend.models.models import DoiTuong

logger = logging.getLogger(__name__)


def search_profiles(
    db: Session,
    query: str = "",
    gioi_tinh: Optional[str] = None,
    dia_chi_xa: Optional[str] = None,
    nghe_nghiep: Optional[str] = None,
    page: int = 1,
    page_size: int = 25,
) -> Dict[str, Any]:
    stmt = select(DoiTuong).where(DoiTuong.is_draft == False)

    if query:
        q = f"%{query}%"
        stmt = stmt.where(or_(
            DoiTuong.cccd.ilike(q),
            DoiTuong.ho_ten.ilike(q),
        ))
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
