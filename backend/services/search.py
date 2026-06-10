import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from backend.models.models import DoiTuong, LienHe, TaiChinh, CCCDHistory
import re

logger = logging.getLogger(__name__)


def lookup_old_cccd(db: Session, cccd_cu: str) -> Optional[str]:
    """Trả CCCD hiện tại nếu cccd_cu tồn tại trong lịch sử đổi CCCD."""
    row = db.execute(
        select(CCCDHistory.cccd_moi).where(CCCDHistory.cccd_cu == cccd_cu).limit(1)
    ).first()
    return row[0] if row else None


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
            try:
                from backend.utils.fuzzy_matching import remove_vietnamese_diacritics
                from sqlalchemy import func, and_
                
                # Each token is separated by comma/semicolon/newline.
                # For each token, we split it into sub-tokens to support multi-word accent-insensitive matching.
                name_or_conds = []
                for t in tokens:
                    t_norm = remove_vietnamese_diacritics(t).lower()
                    sub_tokens = [st for st in t_norm.split() if st]
                    if sub_tokens:
                        name_conds = [func.unaccent_lower(DoiTuong.ho_ten).contains(st) for st in sub_tokens]
                        name_or_conds.append(and_(*name_conds))
                        
                if name_or_conds:
                    or_conditions.append(or_(*name_or_conds))
                else:
                    # Fallback just in case
                    or_conditions.append(DoiTuong.ho_ten.ilike(f"%{query}%"))
            except ImportError:
                or_conditions.append(DoiTuong.ho_ten.ilike(f"%{query}%"))
            
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

    # Tra cứu lịch sử đổi CCCD khi kết quả rỗng và query là CCCD hợp lệ
    cccd_redirect = None
    if total == 0 and query:
        q_stripped = query.strip()
        if re.fullmatch(r'\d{9}|\d{12}', q_stripped):
            cccd_redirect = lookup_old_cccd(db, q_stripped)

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if total else 0,
        "cccd_redirect": cccd_redirect,
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

    # Batch load 1 query IN(...) thay vì db.get() từng kết quả (N+1).
    matched_cccd = [cccd_list[m["index"]] for m in raw_matches]
    dt_map = {
        dt.cccd: dt
        for dt in db.execute(
            select(DoiTuong).where(DoiTuong.cccd.in_(matched_cccd))
        ).scalars()
    } if matched_cccd else {}

    results = []
    for m in raw_matches:
        dt = dt_map.get(cccd_list[m["index"]])
        if dt:
            results.append({
                "cccd": dt.cccd,
                "ho_ten": dt.ho_ten,
                "ngay_sinh": dt.ngay_sinh.strftime("%d/%m/%Y") if dt.ngay_sinh else "",
                "dia_chi_xa": dt.dia_chi_xa or "",
                "score": m["score"],
            })
    return results
