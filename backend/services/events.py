"""
backend/services/events.py — Service xử lý sự kiện & thông báo
"""
from datetime import date, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_

from backend.models.models import QuaTrinhHoatDong, DoiTuong

NOTIFICATION_DAYS = 7  # Ngưỡng thông báo: sự kiện trong vòng 7 ngày tới


def get_upcoming_events(db: Session, days: int = NOTIFICATION_DAYS) -> List[Dict]:
    """
    Lấy danh sách sự kiện sắp đến hạn trong N ngày tới.
    Điều kiện: ngay_ket_thuc nằm trong [hôm nay, hôm nay + N ngày].
    """
    today = date.today()
    deadline = today + timedelta(days=days)

    rows = (
        db.execute(
            select(QuaTrinhHoatDong, DoiTuong.ho_ten)
            .join(DoiTuong, DoiTuong.cccd == QuaTrinhHoatDong.cccd)
            .where(
                and_(
                    QuaTrinhHoatDong.ngay_ket_thuc.isnot(None),
                    QuaTrinhHoatDong.ngay_ket_thuc >= today,
                    QuaTrinhHoatDong.ngay_ket_thuc <= deadline,
                )
            )
            .order_by(QuaTrinhHoatDong.ngay_ket_thuc.asc())
        )
        .all()
    )

    result = []
    for qt, ho_ten in rows:
        days_left = (qt.ngay_ket_thuc - today).days
        result.append({
            "id": qt.id,
            "cccd": qt.cccd,
            "ho_ten": ho_ten or qt.cccd,
            "noi_dung": qt.noi_dung or "",
            "ngay_bat_dau": qt.ngay_bat_dau.strftime("%d/%m/%Y") if qt.ngay_bat_dau else "",
            "ngay_ket_thuc": qt.ngay_ket_thuc.strftime("%d/%m/%Y"),
            "days_left": days_left,
            "is_today": days_left == 0,
            "is_overdue": False,  # Trường hợp này không xảy ra vì lọc >= today
        })

    return result


def count_upcoming_events(db: Session, days: int = NOTIFICATION_DAYS) -> int:
    """Đếm số thông báo sự kiện sắp đến hạn."""
    today = date.today()
    deadline = today + timedelta(days=days)
    count = db.execute(
        select(QuaTrinhHoatDong.id)
        .where(
            and_(
                QuaTrinhHoatDong.ngay_ket_thuc.isnot(None),
                QuaTrinhHoatDong.ngay_ket_thuc >= today,
                QuaTrinhHoatDong.ngay_ket_thuc <= deadline,
            )
        )
    ).all()
    return len(count)


def get_calendar_events(db: Session, month: int, year: int) -> List[Dict]:
    """
    Lấy tất cả sự kiện có ngay_ket_thuc trong tháng/năm chỉ định.
    Trả về danh sách đã group theo ngày (ngay_ket_thuc).
    """
    from calendar import monthrange
    _, last_day = monthrange(year, month)
    month_start = date(year, month, 1)
    month_end = date(year, month, last_day)
    today = date.today()

    rows = (
        db.execute(
            select(QuaTrinhHoatDong, DoiTuong.ho_ten)
            .join(DoiTuong, DoiTuong.cccd == QuaTrinhHoatDong.cccd)
            .where(
                and_(
                    QuaTrinhHoatDong.ngay_ket_thuc.isnot(None),
                    QuaTrinhHoatDong.ngay_ket_thuc >= month_start,
                    QuaTrinhHoatDong.ngay_ket_thuc <= month_end,
                )
            )
            .order_by(QuaTrinhHoatDong.ngay_ket_thuc.asc())
        )
        .all()
    )

    result = []
    for qt, ho_ten in rows:
        deadline = qt.ngay_ket_thuc
        days_left = (deadline - today).days

        if days_left < 0:
            status = "overdue"
        elif days_left <= NOTIFICATION_DAYS:
            status = "upcoming"
        else:
            status = "normal"

        result.append({
            "id": qt.id,
            "cccd": qt.cccd,
            "ho_ten": ho_ten or qt.cccd,
            "noi_dung": qt.noi_dung or "",
            "ngay_bat_dau": qt.ngay_bat_dau.strftime("%d/%m/%Y") if qt.ngay_bat_dau else "",
            "ngay_ket_thuc_str": deadline.strftime("%d/%m/%Y"),
            "ngay_ket_thuc_day": deadline.day,
            "ngay_ket_thuc_month": deadline.month,
            "ngay_ket_thuc_year": deadline.year,
            "days_left": days_left,
            "status": status,
        })

    return result
