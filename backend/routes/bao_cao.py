# File: backend/routes/bao_cao.py
import logging
from datetime import datetime
from io import BytesIO
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from backend.constants import PHAN_LOAI_NGHE_NGHIEP
from backend.db.session import get_db
from backend.deps import require_login
from backend.models.models import DoiTuong, LienHe, TaiChinh

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bao-cao", tags=["bao-cao"])
templates = Jinja2Templates(directory="frontend/templates")


# ── Private helpers ───────────────────────────────────────────────────────────

def _parse_dates(
    tu_ngay: Optional[str], den_ngay: Optional[str]
) -> tuple[Optional[datetime], Optional[datetime]]:
    dt_from = datetime.strptime(tu_ngay, "%Y-%m-%d") if tu_ngay else None
    dt_to = (
        datetime.strptime(den_ngay, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        if den_ngay
        else None
    )
    return dt_from, dt_to


def _query_stats(
    db: Session,
    dt_from: Optional[datetime],
    dt_to: Optional[datetime],
    phan_loai: Optional[str],
) -> dict:
    def base_filter():
        conds = [DoiTuong.is_draft == False]
        if dt_from:
            conds.append(DoiTuong.created_at >= dt_from)
        if dt_to:
            conds.append(DoiTuong.created_at <= dt_to)
        if phan_loai:
            conds.append(DoiTuong.phan_loai_nghe_nghiep == phan_loai)
        return and_(*conds)

    total = db.execute(
        select(func.count(DoiTuong.cccd)).where(base_filter())
    ).scalar_one()

    draft_count = db.execute(
        select(func.count(DoiTuong.cccd)).where(DoiTuong.is_draft == True)
    ).scalar_one()

    co_sdt = db.execute(
        select(func.count(DoiTuong.cccd)).where(
            base_filter(),
            DoiTuong.cccd.in_(select(LienHe.cccd).distinct()),
        )
    ).scalar_one()

    co_stk = db.execute(
        select(func.count(DoiTuong.cccd)).where(
            base_filter(),
            DoiTuong.cccd.in_(select(TaiChinh.cccd).distinct()),
        )
    ).scalar_one()

    phan_loai_rows = db.execute(
        select(DoiTuong.phan_loai_nghe_nghiep, func.count(DoiTuong.cccd))
        .where(base_filter())
        .group_by(DoiTuong.phan_loai_nghe_nghiep)
        .order_by(func.count(DoiTuong.cccd).desc())
    ).all()
    by_phan_loai = {(r[0] or "Không rõ"): r[1] for r in phan_loai_rows}

    month_col = func.strftime("%Y-%m", DoiTuong.created_at)
    month_rows = db.execute(
        select(month_col.label("month"), func.count(DoiTuong.cccd).label("cnt"))
        .where(base_filter(), DoiTuong.created_at.isnot(None))
        .group_by(month_col)
        .order_by(month_col)
        .limit(24)
    ).all()
    by_month = [{"month": r[0], "count": r[1]} for r in month_rows if r[0]]

    gioi_tinh_rows = db.execute(
        select(DoiTuong.gioi_tinh, func.count(DoiTuong.cccd))
        .where(base_filter())
        .group_by(DoiTuong.gioi_tinh)
    ).all()
    by_gioi_tinh = {(r[0] or "Không rõ"): r[1] for r in gioi_tinh_rows}

    dia_ban_rows = db.execute(
        select(DoiTuong.dia_chi_xa, func.count(DoiTuong.cccd))
        .where(
            base_filter(),
            DoiTuong.dia_chi_xa.isnot(None),
            DoiTuong.dia_chi_xa != "",
        )
        .group_by(DoiTuong.dia_chi_xa)
        .order_by(func.count(DoiTuong.cccd).desc())
        .limit(10)
    ).all()
    by_dia_ban = {r[0]: r[1] for r in dia_ban_rows}

    table = [
        {
            "phan_loai": loai,
            "count": cnt,
            "pct": round(cnt / total * 100, 1) if total > 0 else 0,
        }
        for loai, cnt in by_phan_loai.items()
    ]

    return {
        "summary": {
            "total": total,
            "draft": draft_count,
            "co_sdt": co_sdt,
            "co_stk": co_stk,
        },
        "by_phan_loai": by_phan_loai,
        "by_month": by_month,
        "by_gioi_tinh": by_gioi_tinh,
        "by_dia_ban": by_dia_ban,
        "table": table,
    }


def _build_xlsx(stats: dict, filter_lines: list, generated_at: datetime) -> BytesIO:
    from openpyxl import Workbook
    from openpyxl.formatting.rule import DataBarRule
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    wb = Workbook()

    # ── Shared styles ─────────────────────────────────────────────────────────
    _thin = Side(style="thin", color="E2E8F0")
    BORDER = Border(left=_thin, right=_thin, top=_thin, bottom=_thin)
    CENTER = Alignment(horizontal="center", vertical="center")
    LEFT   = Alignment(horizontal="left",   vertical="center", indent=1)
    RIGHT  = Alignment(horizontal="right",  vertical="center")

    TITLE_FONT = Font(bold=True, color="FFFFFF", size=13, name="Calibri")
    TITLE_FILL = PatternFill(fill_type="solid", fgColor="1E40AF")
    TITLE_ALIGN = Alignment(horizontal="center", vertical="center")

    SEC_FONT  = Font(bold=True, color="FFFFFF", size=10, name="Calibri")
    SEC_FILL  = PatternFill(fill_type="solid", fgColor="0F766E")
    SEC_ALIGN = Alignment(horizontal="left", vertical="center", indent=1)

    HDR_FONT  = Font(bold=True, color="1E40AF", size=10, name="Calibri")
    HDR_FILL  = PatternFill(fill_type="solid", fgColor="DBEAFE")

    LABEL_FONT = Font(bold=True, color="334155", size=10, name="Calibri")
    LABEL_FILL = PatternFill(fill_type="solid", fgColor="F1F5F9")
    DATA_FONT  = Font(color="1E293B", size=10, name="Calibri")
    ALT_FILL   = PatternFill(fill_type="solid", fgColor="F8FAFC")
    NUM_FONT   = Font(bold=True, color="1E40AF", size=11, name="Calibri")

    # ── Helper utilities ──────────────────────────────────────────────────────
    def _c(ws, row, col, value=None, *, font=None, fill=None, align=None,
           border=None, fmt=None):
        cell = ws.cell(row=row, column=col, value=value)
        if font   is not None: cell.font      = font
        if fill   is not None: cell.fill      = fill
        if align  is not None: cell.alignment = align
        if border is not None: cell.border    = border
        if fmt    is not None: cell.number_format = fmt
        return cell

    def _title_row(ws, row, ncols, text, is_section=False):
        ws.merge_cells(f"A{row}:{get_column_letter(ncols)}{row}")
        _c(ws, row, 1, text,
           font=SEC_FONT if is_section else TITLE_FONT,
           fill=SEC_FILL if is_section else TITLE_FILL,
           align=SEC_ALIGN if is_section else TITLE_ALIGN)
        ws.row_dimensions[row].height = 30 if not is_section else 22

    def _col_headers(ws, row, headers, widths=None):
        for i, h in enumerate(headers, 1):
            _c(ws, row, i, h, font=HDR_FONT, fill=HDR_FILL,
               align=Alignment(horizontal="center", vertical="center", wrap_text=True),
               border=BORDER)
        if widths:
            for i, w in enumerate(widths, 1):
                ws.column_dimensions[get_column_letter(i)].width = w
        ws.row_dimensions[row].height = 22

    def _data_row(ws, row, values, aligns=None):
        fill = ALT_FILL if row % 2 == 0 else None
        for i, v in enumerate(values, 1):
            a = (aligns[i - 1] if aligns else None) or LEFT
            _c(ws, row, i, v, font=DATA_FONT, fill=fill, align=a, border=BORDER)

    # Pull data
    summary    = stats["summary"]
    by_phan_loai = stats["by_phan_loai"]
    by_month   = stats["by_month"]
    by_gioi_tinh = stats["by_gioi_tinh"]
    by_dia_ban  = stats["by_dia_ban"]
    table      = stats["table"]
    total      = summary["total"]

    # ═══════════════════════════════════════════════════════════════════════════
    # SHEET 1 — Tóm tắt
    # ═══════════════════════════════════════════════════════════════════════════
    ws1 = wb.active
    ws1.title = "Tóm tắt"
    ws1.sheet_view.showGridLines = False

    _title_row(ws1, 1, 3, "BÁO CÁO THỐNG KÊ ĐỐI TƯỢNG")

    ws1.merge_cells("A2:C2")
    _c(ws1, 2, 1, "Security Profile 360 · PA01",
       font=Font(italic=True, color="64748B", size=10, name="Calibri"),
       fill=PatternFill(fill_type="solid", fgColor="F8FAFC"),
       align=CENTER)
    ws1.row_dimensions[2].height = 16

    # Metadata rows
    meta = [
        ("Ngày xuất báo cáo", generated_at.strftime("%d/%m/%Y %H:%M")),
        ("Bộ lọc áp dụng",   " | ".join(filter_lines)),
    ]
    for i, (lbl, val) in enumerate(meta, 3):
        _c(ws1, i, 1, lbl, font=LABEL_FONT, fill=LABEL_FILL, align=LEFT, border=BORDER)
        ws1.merge_cells(f"B{i}:C{i}")
        _c(ws1, i, 2, val, font=DATA_FONT, fill=ALT_FILL, align=LEFT, border=BORDER)

    # Summary section
    _title_row(ws1, 6, 3, "  SỐ LIỆU TỔNG HỢP", is_section=True)

    kpi_rows = [
        ("Tổng hồ sơ hoàn chỉnh",  summary["total"]),
        ("Hồ sơ đang soạn thảo",   summary["draft"]),
        ("Có số điện thoại",        summary["co_sdt"]),
        ("Có tài khoản ngân hàng",  summary["co_stk"]),
    ]
    for i, (lbl, val) in enumerate(kpi_rows, 7):
        _c(ws1, i, 1, lbl, font=LABEL_FONT, fill=LABEL_FILL, align=LEFT, border=BORDER)
        ws1.merge_cells(f"B{i}:C{i}")
        _c(ws1, i, 2, val, font=NUM_FONT,   fill=None, align=CENTER, border=BORDER)

    # Giới tính section
    _title_row(ws1, 12, 3, "  PHÂN BỐ GIỚI TÍNH", is_section=True)
    _col_headers(ws1, 13, ["Giới tính", "Số hồ sơ", "Tỷ lệ (%)"])
    for i, (gt, cnt) in enumerate(by_gioi_tinh.items(), 1):
        pct = round(cnt / total * 100, 1) if total else 0
        _data_row(ws1, 13 + i, [gt, cnt, pct], aligns=[LEFT, CENTER, CENTER])
        ws1.cell(row=13 + i, column=3).number_format = '0.0"%"'

    ws1.column_dimensions["A"].width = 32
    ws1.column_dimensions["B"].width = 22
    ws1.column_dimensions["C"].width = 14

    # ═══════════════════════════════════════════════════════════════════════════
    # SHEET 2 — Phân loại nghề nghiệp
    # ═══════════════════════════════════════════════════════════════════════════
    ws2 = wb.create_sheet("Phân loại NNg")
    ws2.sheet_view.showGridLines = False

    _title_row(ws2, 1, 4, "PHÂN BỐ THEO PHÂN LOẠI NGHỀ NGHIỆP")
    _col_headers(ws2, 2,
                 ["STT", "Phân loại nghề nghiệp", "Số hồ sơ", "Tỷ lệ (%)"],
                 widths=[6, 36, 14, 14])

    for i, row in enumerate(table, 1):
        r = i + 2
        fill = ALT_FILL if i % 2 == 0 else None
        _c(ws2, r, 1, i,             font=DATA_FONT, fill=fill, align=CENTER, border=BORDER)
        _c(ws2, r, 2, row["phan_loai"], font=DATA_FONT, fill=fill, align=LEFT,   border=BORDER)
        _c(ws2, r, 3, row["count"],     font=DATA_FONT, fill=fill, align=CENTER, border=BORDER)
        _c(ws2, r, 4, row["pct"],       font=DATA_FONT, fill=fill, align=CENTER, border=BORDER,
           fmt='0.0"%"')

    if table:
        ws2.freeze_panes = "A3"
        ws2.auto_filter.ref = f"A2:D{2 + len(table)}"
        ws2.conditional_formatting.add(
            f"D3:D{2 + len(table)}",
            DataBarRule(start_type="num", start_value=0,
                        end_type="num",   end_value=100,
                        color="3B82F6"),
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # SHEET 3 — Biến động theo tháng
    # ═══════════════════════════════════════════════════════════════════════════
    ws3 = wb.create_sheet("Biến động tháng")
    ws3.sheet_view.showGridLines = False

    _title_row(ws3, 1, 3, "BIẾN ĐỘNG NHẬP HỒ SƠ THEO THÁNG")
    _col_headers(ws3, 2, ["STT", "Tháng", "Số hồ sơ nhập mới"],
                 widths=[6, 18, 22])

    for i, m in enumerate(by_month, 1):
        r = i + 2
        fill = ALT_FILL if i % 2 == 0 else None
        _c(ws3, r, 1, i,          font=DATA_FONT, fill=fill, align=CENTER, border=BORDER)
        _c(ws3, r, 2, m["month"], font=DATA_FONT, fill=fill, align=CENTER, border=BORDER)
        _c(ws3, r, 3, m["count"], font=DATA_FONT, fill=fill, align=CENTER, border=BORDER)

    if by_month:
        ws3.freeze_panes = "A3"
        ws3.auto_filter.ref = f"A2:C{2 + len(by_month)}"

    # ═══════════════════════════════════════════════════════════════════════════
    # SHEET 4 — Địa bàn
    # ═══════════════════════════════════════════════════════════════════════════
    ws4 = wb.create_sheet("Địa bàn")
    ws4.sheet_view.showGridLines = False

    _title_row(ws4, 1, 3, "TOP 10 ĐỊA BÀN CÓ NHIỀU HỒ SƠ NHẤT")
    _col_headers(ws4, 2, ["STT", "Địa bàn (Xã/Phường)", "Số hồ sơ"],
                 widths=[6, 36, 16])

    for i, (db_name, cnt) in enumerate(by_dia_ban.items(), 1):
        r = i + 2
        fill = ALT_FILL if i % 2 == 0 else None
        _c(ws4, r, 1, i,       font=DATA_FONT, fill=fill, align=CENTER, border=BORDER)
        _c(ws4, r, 2, db_name, font=DATA_FONT, fill=fill, align=LEFT,   border=BORDER)
        _c(ws4, r, 3, cnt,     font=DATA_FONT, fill=fill, align=CENTER, border=BORDER)

    if by_dia_ban:
        ws4.freeze_panes = "A3"
        ws4.auto_filter.ref = f"A2:C{2 + len(by_dia_ban)}"

    # ── Serialize ─────────────────────────────────────────────────────────────
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("", response_class=HTMLResponse)
def bao_cao_page(request: Request, user: dict = Depends(require_login)):
    return templates.TemplateResponse(
        request,
        "bao_cao/index.html",
        {"user": user, "phan_loai_options": PHAN_LOAI_NGHE_NGHIEP},
    )


@router.get("/api/thong-ke")
def api_thong_ke(
    tu_ngay: Optional[str] = Query(None, description="YYYY-MM-DD"),
    den_ngay: Optional[str] = Query(None, description="YYYY-MM-DD"),
    phan_loai: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: dict = Depends(require_login),
):
    try:
        dt_from, dt_to = _parse_dates(tu_ngay, den_ngay)
        return _query_stats(db, dt_from, dt_to, phan_loai)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Lỗi api_thong_ke: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Lỗi thống kê: {exc}")


@router.get("/export-xlsx")
def export_xlsx(
    tu_ngay: Optional[str] = Query(None, description="YYYY-MM-DD"),
    den_ngay: Optional[str] = Query(None, description="YYYY-MM-DD"),
    phan_loai: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: dict = Depends(require_login),
):
    try:
        dt_from, dt_to = _parse_dates(tu_ngay, den_ngay)
        stats = _query_stats(db, dt_from, dt_to, phan_loai)

        filter_lines: list[str] = []
        if tu_ngay:
            filter_lines.append(
                f"Từ ngày: {datetime.strptime(tu_ngay, '%Y-%m-%d').strftime('%d/%m/%Y')}"
            )
        if den_ngay:
            filter_lines.append(
                f"Đến ngày: {datetime.strptime(den_ngay, '%Y-%m-%d').strftime('%d/%m/%Y')}"
            )
        if phan_loai:
            filter_lines.append(f"Phân loại: {phan_loai}")
        if not filter_lines:
            filter_lines = ["Toàn bộ dữ liệu (không lọc)"]

        now = datetime.now()
        buf = _build_xlsx(stats, filter_lines, now)

        filename = f"bao-cao-thong-ke-{now.strftime('%Y%m%d-%H%M')}.xlsx"
        return StreamingResponse(
            buf,
            media_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Lỗi export_xlsx: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Lỗi xuất Excel: {exc}")
