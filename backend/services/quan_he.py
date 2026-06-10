from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional, Tuple

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.constants import LOAI_QUAN_HE_DEF, get_quan_he_label
from backend.models.models import DoiTuong, NhanThan, QuanHeDoiTuong


def get_quan_he_full(db: Session, cccd: str) -> List[Dict]:
    """Gộp graph edges + satellite (nhan_than), render đúng chiều."""
    items: List[Dict] = []

    edges = db.execute(
        select(QuanHeDoiTuong).where(
            or_(QuanHeDoiTuong.cccd_1 == cccd, QuanHeDoiTuong.cccd_2 == cccd)
        )
    ).scalars().all()

    # Batch load toàn bộ đối tác bằng 1 query IN(...) thay vì db.get()
    # từng cạnh (N+1) — hồ sơ nhiều quan hệ sẽ chậm rõ rệt.
    doi_tac_cccds = {
        edge.cccd_2 if edge.cccd_1 == cccd else edge.cccd_1 for edge in edges
    }
    doi_tac_map = {
        dt.cccd: dt
        for dt in db.execute(
            select(DoiTuong).where(DoiTuong.cccd.in_(doi_tac_cccds))
        ).scalars()
    } if doi_tac_cccds else {}

    for edge in edges:
        is_cccd1 = edge.cccd_1 == cccd
        cccd_doi_tac = edge.cccd_2 if is_cccd1 else edge.cccd_1
        label = get_quan_he_label(edge.loai_quan_he, 1 if is_cccd1 else 2)
        doi_tac = doi_tac_map.get(cccd_doi_tac)
        items.append({
            "type": "graph",
            "edge_id": edge.id,
            "cccd_doi_tac": cccd_doi_tac,
            "ho_ten": doi_tac.ho_ten if doi_tac else None,
            "is_draft": doi_tac.is_draft if doi_tac else False,
            "loai_quan_he": edge.loai_quan_he,
            "label": label,
            "mo_ta": edge.mo_ta,
        })

    satellites = db.execute(
        select(NhanThan).where(NhanThan.cccd == cccd)
    ).scalars().all()

    for nt in satellites:
        items.append({
            "type": "satellite",
            "item_id": nt.id,
            "ho_ten": nt.ho_ten,
            "loai_quan_he": nt.loai_quan_he,
            "label": nt.loai_quan_he,
            "cccd_doi_tac": None,
            "is_draft": False,
            "quoc_tich": nt.quoc_tich,
            "mo_ta": nt.ghi_chu,
        })

    return items


def add_quan_he_co_cccd(db: Session, cccd_chinh: str, data: Dict) -> Tuple[bool, str]:
    """Tạo edge + auto tạo DoiTuong nếu chưa có (race-safe)."""
    cccd_doi_tac: str = (data.get("cccd_doi_tac") or "").strip()
    loai: str = data.get("loai_quan_he", "")

    if not loai:
        return False, "Vui lòng chọn loại quan hệ"
    if not cccd_doi_tac:
        return False, "Vui lòng nhập CCCD đối tác"
    if cccd_doi_tac == cccd_chinh:
        return False, "Không thể tự liên kết với chính mình"

    doi_tac = db.get(DoiTuong, cccd_doi_tac)
    if not doi_tac:
        ho_ten: Optional[str] = (data.get("ho_ten") or "").strip().upper() or None
        doi_tac = DoiTuong(
            cccd=cccd_doi_tac,
            is_draft=not bool(ho_ten),
            ho_ten=ho_ten,
            ngay_sinh=_parse_date(data.get("ngay_sinh")),
            gioi_tinh=data.get("gioi_tinh") or None,
            dan_toc=data.get("dan_toc") or None,
            ton_giao=data.get("ton_giao") or None,
            quoc_tich=data.get("quoc_tich") or None,
            dia_chi_tinh=data.get("dia_chi_tinh") or None,
            dia_chi_xa=data.get("dia_chi_xa") or None,
            phan_loai_nghe_nghiep=data.get("phan_loai_nghe_nghiep") or None,
            chi_tiet_nghe_nghiep=data.get("chi_tiet_nghe_nghiep") or None,
        )
        try:
            db.add(doi_tac)
            db.flush()
        except IntegrityError:
            db.rollback()
            doi_tac = db.get(DoiTuong, cccd_doi_tac)
    else:
        if not doi_tac.ho_ten and data.get("ho_ten"):
            doi_tac.ho_ten = data["ho_ten"].strip().upper()

    cccd_1, cccd_2, loai_chuan = _chuan_hoa_cap(cccd_chinh, cccd_doi_tac, loai)
    try:
        db.add(QuanHeDoiTuong(cccd_1=cccd_1, cccd_2=cccd_2, loai_quan_he=loai_chuan, mo_ta=data.get("mo_ta") or None))
        db.commit()
    except IntegrityError:
        db.rollback()
        return False, "Quan hệ này đã tồn tại"
    return True, "Đã thêm quan hệ"


def add_quan_he_khong_cccd(db: Session, cccd_chinh: str, data: Dict) -> Tuple[bool, str]:
    """Insert vào nhan_than (fallback cho người không có CCCD)."""
    loai = data.get("loai_quan_he", "")
    if not loai:
        return False, "Vui lòng chọn loại quan hệ"
    db.add(NhanThan(
        cccd=cccd_chinh,
        loai_quan_he=loai,
        ho_ten=(data.get("ho_ten") or "").strip().upper() or None,
        gioi_tinh=data.get("gioi_tinh") or None,
        quoc_tich=data.get("quoc_tich") or None,
        dia_chi_tinh=data.get("dia_chi_tinh") or None,
        dia_chi_xa=data.get("dia_chi_xa") or None,
        nghe_nghiep=data.get("nghe_nghiep") or None,
        ghi_chu=data.get("mo_ta") or None,
    ))
    db.commit()
    return True, "Đã thêm ghi chú quan hệ"


def delete_quan_he_graph(db: Session, cccd_chinh: str, edge_id: int) -> Tuple[bool, str]:
    """Xóa edge + auto-clean nháp mồ côi."""
    edge = db.get(QuanHeDoiTuong, edge_id)
    if not edge:
        return False, "Không tìm thấy quan hệ"
    if edge.cccd_1 != cccd_chinh and edge.cccd_2 != cccd_chinh:
        return False, "Không có quyền xóa quan hệ này"

    cccd_doi_tac = edge.cccd_2 if edge.cccd_1 == cccd_chinh else edge.cccd_1
    db.delete(edge)
    db.flush()  # tránh stale read khi check orphan

    doi_tac = db.get(DoiTuong, cccd_doi_tac)
    if doi_tac and doi_tac.is_draft and _is_orphan_draft(db, cccd_doi_tac):
        db.delete(doi_tac)
    db.commit()
    return True, "Đã xóa quan hệ"


def delete_quan_he_satellite(db: Session, item_id: int) -> Tuple[bool, str]:
    """Xóa ghi chú nhân thân (satellite)."""
    nt = db.get(NhanThan, item_id)
    if not nt:
        return False, "Không tìm thấy"
    db.delete(nt)
    db.commit()
    return True, "Đã xóa"


def preview_cccd(db: Session, cccd: str) -> Dict:
    """Trả thông tin hồ sơ (nếu có) để autofill form."""
    doi_tac = db.get(DoiTuong, cccd)
    if not doi_tac:
        return {"has_profile": False}
    return {
        "has_profile": True,
        "ho_ten": doi_tac.ho_ten,
        "ngay_sinh": doi_tac.ngay_sinh.strftime("%Y-%m-%d") if doi_tac.ngay_sinh else "",
        "is_draft": doi_tac.is_draft,
    }


def _chuan_hoa_cap(cccd_a: str, cccd_b: str, loai: str) -> Tuple[str, str, str]:
    """Đối xứng → chuẩn hóa min/max; có hướng → giữ nguyên thứ tự."""
    if LOAI_QUAN_HE_DEF.get(loai, {}).get("doi_xung", True):
        return (min(cccd_a, cccd_b), max(cccd_a, cccd_b), loai)
    return (cccd_a, cccd_b, loai)


def _is_orphan_draft(db: Session, cccd: str) -> bool:
    """True nếu hồ sơ is_draft=True VÀ không còn edge VÀ không còn satellite."""
    has_edge = db.execute(
        select(QuanHeDoiTuong.id).where(
            or_(QuanHeDoiTuong.cccd_1 == cccd, QuanHeDoiTuong.cccd_2 == cccd)
        ).limit(1)
    ).first()
    if has_edge:
        return False
    has_satellite = db.execute(
        select(NhanThan.id).where(NhanThan.cccd == cccd).limit(1)
    ).first()
    return not bool(has_satellite)


def _parse_date(val) -> Optional[date]:
    if not val:
        return None
    try:
        return date.fromisoformat(val)
    except (ValueError, TypeError):
        return None
