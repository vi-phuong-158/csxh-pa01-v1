import logging
from datetime import datetime
from typing import Dict, Any
from cachetools import TTLCache, cached
from sqlalchemy.orm import Session
from sqlalchemy import select, func, text

from backend.models.models import DoiTuong, HoSoDacThu, AuditLog

logger = logging.getLogger(__name__)

_stats_cache: TTLCache = TTLCache(maxsize=1, ttl=300)


def get_statistics(db: Session) -> Dict[str, Any]:
    try:
        total = db.execute(
            select(func.count(DoiTuong.cccd)).where(DoiTuong.is_draft == False)
        ).scalar_one()

        gioi_tinh_rows = db.execute(
            select(DoiTuong.gioi_tinh, func.count(DoiTuong.cccd))
            .where(DoiTuong.is_draft == False)
            .group_by(DoiTuong.gioi_tinh)
        ).all()

        nghe_nghiep_rows = db.execute(
            select(DoiTuong.phan_loai_nghe_nghiep, func.count(DoiTuong.cccd))
            .where(DoiTuong.is_draft == False)
            .group_by(DoiTuong.phan_loai_nghe_nghiep)
        ).all()

        dac_thu_rows = db.execute(
            select(HoSoDacThu.loai_hinh, func.count(HoSoDacThu.id))
            .group_by(HoSoDacThu.loai_hinh)
        ).all()

        dia_ban_rows = db.execute(
            select(DoiTuong.dia_chi_xa, func.count(DoiTuong.cccd))
            .where(DoiTuong.is_draft == False, DoiTuong.dia_chi_xa.isnot(None))
            .group_by(DoiTuong.dia_chi_xa)
            .order_by(func.count(DoiTuong.cccd).desc())
            .limit(10)
        ).all()

        return {
            "total": total,
            "gioi_tinh": {row[0] or "Không rõ": row[1] for row in gioi_tinh_rows},
            "nghe_nghiep": {row[0] or "Không rõ": row[1] for row in nghe_nghiep_rows},
            "dac_thu": {row[0]: row[1] for row in dac_thu_rows},
            "dia_ban": {row[0]: row[1] for row in dia_ban_rows},
        }
    except Exception as e:
        logger.error(f"Lỗi get_statistics: {e}")
        return {"total": 0, "gioi_tinh": {}, "nghe_nghiep": {}, "dac_thu": {}, "dia_ban": {}}


def get_recent_records(db: Session, limit: int = 10):
    rows = db.execute(
        select(DoiTuong)
        .where(DoiTuong.is_draft == False)
        .order_by(DoiTuong.created_at.desc())
        .limit(limit)
    ).scalars().all()
    return [
        {
            "cccd": r.cccd,
            "ho_ten": r.ho_ten,
            "ngay_sinh": r.ngay_sinh.strftime("%d/%m/%Y") if r.ngay_sinh else "",
            "gioi_tinh": r.gioi_tinh,
            "dia_chi_xa": r.dia_chi_xa,
            "phan_loai_nghe_nghiep": r.phan_loai_nghe_nghiep,
            "created_at": r.created_at.strftime("%d/%m/%Y %H:%M") if r.created_at else "",
        }
        for r in rows
    ]


def get_recent_audit(db: Session, limit: int = 20):
    rows = db.execute(
        select(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    ).scalars().all()
    return [
        {
            "id": r.id,
            "bang": r.bang,
            "hanh_dong": r.hanh_dong,
            "khoa_chinh": r.khoa_chinh,
            "nguoi_thuc_hien": r.nguoi_thuc_hien,
            "created_at": r.created_at.strftime("%d/%m/%Y %H:%M") if r.created_at else "",
        }
        for r in rows
    ]
