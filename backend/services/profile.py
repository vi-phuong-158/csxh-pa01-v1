import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.models.models import (
    DoiTuong, LienHe, TaiChinh, PhuongTien, NhanThan,
    HoSoDacThu, TaiLieu, QuaTrinhHoatDong, AuditLog,
)
from backend.config import settings

logger = logging.getLogger(__name__)


def get_profile(db: Session, cccd: str) -> Optional[DoiTuong]:
    return db.get(DoiTuong, cccd)


def get_profile_full(db: Session, cccd: str) -> Optional[Dict]:
    dt = db.get(DoiTuong, cccd)
    if not dt:
        return None
    return {
        "cccd": dt.cccd,
        "ho_ten": dt.ho_ten,
        "ngay_sinh": dt.ngay_sinh.strftime("%Y-%m-%d") if dt.ngay_sinh else "",
        "gioi_tinh": dt.gioi_tinh,
        "dia_chi_tinh": dt.dia_chi_tinh,
        "dia_chi_xa": dt.dia_chi_xa,
        "anh_chan_dung": dt.anh_chan_dung,
        "phan_loai_nghe_nghiep": dt.phan_loai_nghe_nghiep,
        "chi_tiet_nghe_nghiep": dt.chi_tiet_nghe_nghiep,
        "ghi_chu_chung": dt.ghi_chu_chung,
        "is_draft": dt.is_draft,
        "created_at": dt.created_at.strftime("%d/%m/%Y %H:%M") if dt.created_at else "",
        "updated_at": dt.updated_at.strftime("%d/%m/%Y %H:%M") if dt.updated_at else "",
        "lien_he": [{"id": x.id, "loai": x.loai_lien_he, "gia_tri": x.gia_tri, "ghi_chu": x.ghi_chu} for x in dt.lien_he],
        "tai_chinh": [{"id": x.id, "ngan_hang": x.ngan_hang, "so_tai_khoan": x.so_tai_khoan, "chu": x.chu_tai_khoan, "ghi_chu": x.ghi_chu} for x in dt.tai_chinh],
        "phuong_tien": [{"id": x.id, "loai_xe": x.loai_xe, "bien": x.bien_kiem_soat, "ten": x.ten_phuong_tien, "ghi_chu": x.ghi_chu} for x in dt.phuong_tien],
        "nhan_than": [{"id": x.id, "quan_he": x.loai_quan_he, "ho_ten": x.ho_ten, "cccd": x.cccd_nhan_than, "ngay_sinh": x.ngay_sinh.strftime("%Y-%m-%d") if x.ngay_sinh else "", "gioi_tinh": x.gioi_tinh, "nghe_nghiep": x.nghe_nghiep, "noi_o": x.noi_o, "dia_chi_tinh": x.dia_chi_tinh, "dia_chi_xa": x.dia_chi_xa, "ghi_chu": x.ghi_chu} for x in dt.nhan_than],
        "ho_so_dac_thu": [{"id": x.id, "loai_hinh": x.loai_hinh, "noi_dung": x.noi_dung_chi_tiet, "ghi_chu": x.ghi_chu} for x in dt.ho_so_dac_thu],
        "tai_lieu": [{"id": x.id, "ten_goc": x.ten_file_goc, "duong_dan": x.duong_dan, "loai": x.loai_tai_lieu, "mo_ta": x.mo_ta} for x in dt.tai_lieu],
        "qua_trinh": [{"id": x.id, "thoi_gian": x.thoi_gian, "noi_dung": x.noi_dung, "ghi_chu": x.ghi_chu} for x in dt.qua_trinh],
    }


def create_draft(db: Session, cccd: str) -> Tuple[bool, str]:
    dt = db.get(DoiTuong, cccd)
    if dt:
        return True, cccd
    db.add(DoiTuong(cccd=cccd, is_draft=True))
    db.commit()
    return True, cccd


def update_basic_info(db: Session, cccd: str, data: Dict, nguoi: str = "") -> Tuple[bool, str]:
    dt = db.get(DoiTuong, cccd)
    if not dt:
        return False, "Không tìm thấy hồ sơ"
    old = {"ho_ten": dt.ho_ten, "ngay_sinh": str(dt.ngay_sinh)}
    for field in ["ho_ten", "gioi_tinh", "dia_chi_tinh", "dia_chi_xa",
                  "phan_loai_nghe_nghiep", "chi_tiet_nghe_nghiep", "ghi_chu_chung"]:
        if field in data:
            setattr(dt, field, data[field] or None)
    if "ngay_sinh" in data and data["ngay_sinh"]:
        try:
            dt.ngay_sinh = datetime.strptime(data["ngay_sinh"], "%Y-%m-%d").date()
        except ValueError:
            pass
    _log(db, "doi_tuong", "UPDATE", cccd, str(old), str(data), nguoi)
    db.commit()
    return True, "Cập nhật thành công"


def commit_draft(db: Session, cccd: str) -> Tuple[bool, str]:
    dt = db.get(DoiTuong, cccd)
    if not dt:
        return False, "Không tìm thấy hồ sơ"
    if not dt.ho_ten:
        return False, "Bắt buộc phải có họ tên"
    dt.is_draft = False
    db.commit()
    return True, "Hoàn tất nhập liệu"


def delete_profile(db: Session, cccd: str, nguoi: str = "") -> Tuple[bool, str]:
    dt = db.get(DoiTuong, cccd)
    if not dt:
        return False, "Không tìm thấy hồ sơ"
    _log(db, "doi_tuong", "DELETE", cccd, f"ho_ten={dt.ho_ten}", None, nguoi)
    db.delete(dt)
    db.commit()
    upload_folder = Path(settings.BASE_DIR) / settings.UPLOAD_DIR / cccd
    if upload_folder.exists():
        shutil.rmtree(upload_folder)
    return True, "Đã xóa hồ sơ"


# ---------- Satellite CRUD ----------

def add_nhan_than(db: Session, cccd: str, data: Dict) -> Tuple[bool, str]:
    db.add(NhanThan(
        cccd=cccd,
        loai_quan_he=data.get("loai_quan_he", ""),
        ho_ten=data.get("ho_ten"),
        cccd_nhan_than=data.get("cccd_nhan_than"),
        ngay_sinh=_parse_date(data.get("ngay_sinh")),
        gioi_tinh=data.get("gioi_tinh", ""),
        dia_chi_tinh=data.get("dia_chi_tinh", ""),
        dia_chi_xa=data.get("dia_chi_xa", ""),
        nghe_nghiep=data.get("nghe_nghiep"),
        noi_o=data.get("noi_o"),
        ghi_chu=data.get("ghi_chu"),
    ))
    db.commit()
    return True, "Đã thêm nhân thân"


def delete_nhan_than(db: Session, item_id: int) -> bool:
    item = db.get(NhanThan, item_id)
    if item:
        db.delete(item)
        db.commit()
        return True
    return False


def add_lien_he(db: Session, cccd: str, data: Dict) -> Tuple[bool, str]:
    db.add(LienHe(cccd=cccd, loai_lien_he=data.get("loai_lien_he"), gia_tri=data.get("gia_tri"), ghi_chu=data.get("ghi_chu")))
    db.commit()
    return True, "Đã thêm liên hệ"


def delete_lien_he(db: Session, item_id: int) -> bool:
    item = db.get(LienHe, item_id)
    if item:
        db.delete(item)
        db.commit()
        return True
    return False


def add_tai_chinh(db: Session, cccd: str, data: Dict) -> Tuple[bool, str]:
    db.add(TaiChinh(cccd=cccd, ngan_hang=data.get("ngan_hang"), so_tai_khoan=data.get("so_tai_khoan"), chu_tai_khoan=data.get("chu_tai_khoan"), ghi_chu=data.get("ghi_chu")))
    db.commit()
    return True, "Đã thêm tài chính"


def delete_tai_chinh(db: Session, item_id: int) -> bool:
    item = db.get(TaiChinh, item_id)
    if item:
        db.delete(item)
        db.commit()
        return True
    return False


def add_phuong_tien(db: Session, cccd: str, data: Dict) -> Tuple[bool, str]:
    db.add(PhuongTien(cccd=cccd, loai_xe=data.get("loai_xe"), bien_kiem_soat=data.get("bien_kiem_soat"), ten_phuong_tien=data.get("ten_phuong_tien"), ghi_chu=data.get("ghi_chu")))
    db.commit()
    return True, "Đã thêm phương tiện"


def delete_phuong_tien(db: Session, item_id: int) -> bool:
    item = db.get(PhuongTien, item_id)
    if item:
        db.delete(item)
        db.commit()
        return True
    return False


def add_ho_so_dac_thu(db: Session, cccd: str, data: Dict) -> Tuple[bool, str]:
    db.add(HoSoDacThu(cccd=cccd, loai_hinh=data.get("loai_hinh", ""), noi_dung_chi_tiet=data.get("noi_dung_chi_tiet"), ghi_chu=data.get("ghi_chu")))
    db.commit()
    return True, "Đã thêm hồ sơ đặc thù"


def delete_ho_so_dac_thu(db: Session, item_id: int) -> bool:
    item = db.get(HoSoDacThu, item_id)
    if item:
        db.delete(item)
        db.commit()
        return True
    return False


def add_qua_trinh(db: Session, cccd: str, data: Dict) -> Tuple[bool, str]:
    db.add(QuaTrinhHoatDong(cccd=cccd, thoi_gian=data.get("thoi_gian"), noi_dung=data.get("noi_dung"), ghi_chu=data.get("ghi_chu")))
    db.commit()
    return True, "Đã thêm quá trình"


def delete_qua_trinh(db: Session, item_id: int) -> bool:
    item = db.get(QuaTrinhHoatDong, item_id)
    if item:
        db.delete(item)
        db.commit()
        return True
    return False


def delete_tai_lieu(db: Session, item_id: int) -> bool:
    item = db.get(TaiLieu, item_id)
    if item:
        if item.duong_dan:
            fp = Path(settings.BASE_DIR) / item.duong_dan
            if fp.exists():
                fp.unlink()
        db.delete(item)
        db.commit()
        return True
    return False


# ---------- helpers ----------

def _parse_date(val):
    if not val:
        return None
    try:
        return datetime.strptime(val, "%Y-%m-%d").date()
    except ValueError:
        return None


def _log(db, bang, hanh_dong, khoa, cu, moi, nguoi):
    try:
        db.add(AuditLog(bang=bang, hanh_dong=hanh_dong, khoa_chinh=khoa,
                        du_lieu_cu=cu, du_lieu_moi=moi, nguoi_thuc_hien=nguoi))
    except Exception:
        pass
