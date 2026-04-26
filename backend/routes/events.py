"""
backend/routes/events.py — Route cho thông báo sự kiện & trang lịch
"""
from datetime import date
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.routes.auth import require_login
import backend.services.events as events_svc

router = APIRouter(prefix="", tags=["events"])
templates = Jinja2Templates(directory="frontend/templates")


@router.get("/api/events/count", response_class=JSONResponse)
def api_event_count(
    db: Session = Depends(get_db),
    user: dict = Depends(require_login),
):
    """Trả về số lượng sự kiện sắp đến hạn (dùng cho badge chuông)."""
    count = events_svc.count_upcoming_events(db)
    return {"count": count}


@router.get("/api/events/notifications", response_class=JSONResponse)
def api_event_notifications(
    db: Session = Depends(get_db),
    user: dict = Depends(require_login),
):
    """Trả về danh sách sự kiện sắp đến hạn (dùng cho dropdown chuông)."""
    events = events_svc.get_upcoming_events(db)
    return {"events": events}


@router.get("/lich-su-kien", response_class=HTMLResponse)
def lich_su_kien(
    request: Request,
    month: int = 0,
    year: int = 0,
    db: Session = Depends(get_db),
    user: dict = Depends(require_login),
):
    """Trang lịch sự kiện toàn hệ thống."""
    today = date.today()
    if not month:
        month = today.month
    if not year:
        year = today.year

    # Điều hướng tháng hợp lệ
    month = max(1, min(12, month))
    year = max(2020, min(2100, year))

    events = events_svc.get_calendar_events(db, month, year)

    # Tính tháng trước / tháng sau
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    # Build calendar grid (tuần bắt đầu từ Thứ Hai)
    import calendar
    cal = calendar.monthcalendar(year, month)

    # Nhóm sự kiện theo ngày trong tháng
    events_by_day: dict = {}
    for ev in events:
        d = ev["ngay_ket_thuc_day"]
        events_by_day.setdefault(d, []).append(ev)

    return templates.TemplateResponse(
        "lich_su_kien/index.html",
        {
            "request": request,
            "user": user,
            "month": month,
            "year": year,
            "month_name": [
                "", "Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4",
                "Tháng 5", "Tháng 6", "Tháng 7", "Tháng 8",
                "Tháng 9", "Tháng 10", "Tháng 11", "Tháng 12",
            ][month],
            "cal": cal,
            "events_by_day": events_by_day,
            "today_day": today.day if today.month == month and today.year == year else -1,
            "prev_month": prev_month,
            "prev_year": prev_year,
            "next_month": next_month,
            "next_year": next_year,
            "upcoming_events": events_svc.get_upcoming_events(db),
        },
    )
