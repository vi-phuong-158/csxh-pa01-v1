import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import select, update as sa_update, func as sa_func

from backend.models.models import (
    DoiTuong, LienHe, TaiChinh, PhuongTien, NhanThan,
    HoSoDacThu, TaiLieu, QuaTrinhHoatDong, AuditLog,
    QuanHeDoiTuong, CCCDHistory,
)
from backend.services import quan_he as qh_svc
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
        "dan_toc": dt.dan_toc,
        "ton_giao": dt.ton_giao,
        "que_quan": dt.que_quan,
        "noi_o_hien_nay": dt.noi_o_hien_nay,
        "quoc_tich": dt.quoc_tich,
        "is_draft": dt.is_draft,
        "created_at": dt.created_at.strftime("%d/%m/%Y %H:%M") if dt.created_at else "",
        "updated_at": dt.updated_at.strftime("%d/%m/%Y %H:%M") if dt.updated_at else "",
        "lien_he": [{"id": x.id, "loai": x.loai_lien_he, "gia_tri": x.gia_tri, "ghi_chu": x.ghi_chu} for x in dt.lien_he],
        "tai_chinh": [{"id": x.id, "ngan_hang": x.ngan_hang, "so_tai_khoan": x.so_tai_khoan, "chu": x.chu_tai_khoan, "ghi_chu": x.ghi_chu} for x in dt.tai_chinh],
        "phuong_tien": [{"id": x.id, "loai_xe": x.loai_xe, "bien": x.bien_kiem_soat, "ten": x.ten_phuong_tien, "ghi_chu": x.ghi_chu} for x in dt.phuong_tien],
        "quan_he": qh_svc.get_quan_he_full(db, cccd),
        "ho_so_dac_thu": [{"id": x.id, "loai_hinh": x.loai_hinh, "noi_dung": x.noi_dung_chi_tiet, "ghi_chu": x.ghi_chu} for x in dt.ho_so_dac_thu],
        "tai_lieu": [{"id": x.id, "ten_goc": x.ten_file_goc, "duong_dan": x.duong_dan, "loai": x.loai_tai_lieu, "mo_ta": x.mo_ta} for x in dt.tai_lieu],
        "qua_trinh": [{
            "id": x.id,
            "thoi_gian": x.thoi_gian,
            "ngay_bat_dau": x.ngay_bat_dau.strftime("%d/%m/%Y") if x.ngay_bat_dau else "",
            "ngay_ket_thuc": x.ngay_ket_thuc.strftime("%d/%m/%Y") if x.ngay_ket_thuc else "",
            "noi_dung": x.noi_dung,
            "ghi_chu": x.ghi_chu,
        } for x in dt.qua_trinh],
    }


def create_draft(db: Session, cccd: str) -> Tuple[bool, str]:
    dt = db.get(DoiTuong, cccd)
    if dt:
        return True, cccd
    db.add(DoiTuong(cccd=cccd, is_draft=True))
    db.commit()
    return True, cccd


def update_basic_info(db: Session, cccd: str, data: Dict, nguoi: str = "") -> Tuple[bool, str]:
    from backend.utils.validators import redact_sensitive
    dt = db.get(DoiTuong, cccd)
    if not dt:
        return False, "Không tìm thấy hồ sơ"
    old = {"ho_ten": dt.ho_ten, "ngay_sinh": str(dt.ngay_sinh)}
    for field in ["ho_ten", "gioi_tinh", "dia_chi_tinh", "dia_chi_xa",
                  "phan_loai_nghe_nghiep", "chi_tiet_nghe_nghiep", "ghi_chu_chung",
                  "dan_toc", "ton_giao", "que_quan", "noi_o_hien_nay", "quoc_tich"]:
        if field in data:
            val = data[field] or None
            if field == "ho_ten" and val:
                val = val.upper()
            setattr(dt, field, val)
    if "ngay_sinh" in data and data["ngay_sinh"]:
        try:
            dt.ngay_sinh = datetime.strptime(data["ngay_sinh"], "%Y-%m-%d").date()
        except ValueError:
            pass
    # F-18: redact field nhạy cảm (password, csrf token...) trước khi lưu
    # audit log. Form thực tế không gửi password ở route này, nhưng nếu
    # frontend bị đổi để lẫn _csrf vào body, log cũ sẽ leak token.
    _log(db, "doi_tuong", "UPDATE", cccd, str(old), str(redact_sensitive(data)), nguoi)
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
    """
    Xoá hồ sơ + dọn dẹp file đính kèm trên đĩa.

    F-04 fix: dù cccd ĐÃ được route layer validate (regex 9/12 số), service
    này vẫn thực hiện kiểm tra prefix ĐỘC LẬP trước khi gọi shutil.rmtree —
    defense-in-depth: nếu sau này có code path khác gọi service trực tiếp
    với cccd lạ, file system vẫn an toàn.
    """
    from backend.utils.validators import validate_cccd

    # Defense-in-depth: nếu service được gọi từ nơi không qua route layer,
    # vẫn raise HTTPException(400) — caller sẽ tự handle.
    validate_cccd(cccd)

    dt = db.get(DoiTuong, cccd)
    if not dt:
        return False, "Không tìm thấy hồ sơ"
    _log(db, "doi_tuong", "DELETE", cccd, f"ho_ten={dt.ho_ten}", None, nguoi)
    db.delete(dt)
    db.commit()

    # Resolve absolute path; sau đó verify rằng cây thư mục đích vẫn nằm
    # bên trong upload_root. Bằng việc check qua relative_to, dù cccd
    # chứa "../../etc" cũng sẽ bị bắt ở đây và bỏ qua bước rmtree.
    upload_root = (Path(settings.BASE_DIR) / settings.UPLOAD_DIR).resolve()
    for sub in ("avatars", "docs"):
        target = (upload_root / sub / cccd).resolve()
        try:
            target.relative_to(upload_root)
        except ValueError:
            # target leak ra ngoài upload_root -> bỏ qua an toàn, không xoá
            continue
        if target.exists() and target.is_dir():
            shutil.rmtree(target)

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
        dan_toc=data.get("dan_toc"),
        ton_giao=data.get("ton_giao"),
        quoc_tich=data.get("quoc_tich"),
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
    loai_hinh = data.get("loai_hinh", "")
    noi_dung = data.get("noi_dung_chi_tiet", "")
    
    if loai_hinh == "Hon_Nhan_NN":
        parts = []
        if data.get("hn_ten"): parts.append(f"Họ tên đối tác: {data.get('hn_ten')}")
        if data.get("hn_qt"): parts.append(f"Quốc tịch: {data.get('hn_qt')}")
        if data.get("hn_hc"): parts.append(f"Số hộ chiếu: {data.get('hn_hc')}")
        if data.get("hn_tt"):    parts.append(f"Tình trạng: {data.get('hn_tt')}")
        if data.get("hn_dc_ht"): parts.append(f"Địa chỉ hiện tại: {data.get('hn_dc_ht')}")
        if data.get("hn_ntr"):   parts.append(f"Nơi thường trú: {data.get('hn_ntr')}")
        if data.get("hn_nghe"):  parts.append(f"Nghề nghiệp: {data.get('hn_nghe')}")
        if data.get("hn_nlv"):   parts.append(f"Nơi làm việc: {data.get('hn_nlv')}")
        if data.get("hn_cv"):    parts.append(f"Chức vụ/vị trí: {data.get('hn_cv')}")
        if parts: noi_dung = "\n".join(parts)
    elif loai_hinh == "Lam_Viec_NN":
        parts = []
        if data.get("lv_tc"): parts.append(f"Tên tổ chức NGO/FDI: {data.get('lv_tc')}")
        if data.get("lv_cv"): parts.append(f"Chức vụ: {data.get('lv_cv')}")
        if data.get("lv_tg"): parts.append(f"Thời gian: {data.get('lv_tg')}")
        if data.get("lv_dd"): parts.append(f"Địa điểm: {data.get('lv_dd')}")
        if parts: noi_dung = "\n".join(parts)
    elif loai_hinh == "Hoc_Tap_Cong_Tac_NN":
        parts = []
        if data.get("ht_dien"): parts.append(f"Diện đi: {data.get('ht_dien')}")
        if data.get("ht_qg"): parts.append(f"Quốc gia: {data.get('ht_qg')}")
        if data.get("ht_tgd"): parts.append(f"Thời gian đi: {data.get('ht_tgd')}")
        if data.get("ht_tgv"): parts.append(f"Thời gian về: {data.get('ht_tgv')}")
        if data.get("ht_nghe"): parts.append(f"Nghề nghiệp sau khi về: {data.get('ht_nghe')}")
        if data.get("ht_dc"):   parts.append(f"Địa chỉ cụ thể: {data.get('ht_dc')}")
        if parts: noi_dung = "\n".join(parts)
    elif loai_hinh == "Vi_Pham_NN":
        parts = []
        if data.get("vp_qg"): parts.append(f"Quốc gia vi phạm: {data.get('vp_qg')}")
        if data.get("vp_cq"): parts.append(f"Cơ quan bắt giữ: {data.get('vp_cq')}")
        if data.get("vp_tg"): parts.append(f"Ngày vi phạm: {_fmt_date_display(data.get('vp_tg'))}")
        if data.get("vp_ht"): parts.append(f"Hình thức xử lý: {data.get('vp_ht')}")
        if data.get("vp_nd"): parts.append(f"Nội dung vi phạm: {data.get('vp_nd')}")
        if parts: noi_dung = "\n".join(parts)
    elif loai_hinh == "Xac_Minh":
        parts = []
        if data.get("xm_cq"): parts.append(f"Cơ quan xác minh: {data.get('xm_cq')}")
        if data.get("xm_tg"): parts.append(f"Ngày xác minh: {_fmt_date_display(data.get('xm_tg'))}")
        if data.get("xm_kq"): parts.append(f"Kết quả: {data.get('xm_kq')}")
        if data.get("xm_nd"): parts.append(f"Nội dung xác minh: {data.get('xm_nd')}")
        if parts: noi_dung = "\n".join(parts)

    db.add(HoSoDacThu(cccd=cccd, loai_hinh=loai_hinh, noi_dung_chi_tiet=noi_dung, ghi_chu=data.get("ghi_chu")))
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
    db.add(QuaTrinhHoatDong(
        cccd=cccd,
        thoi_gian=data.get("thoi_gian"),
        ngay_bat_dau=_parse_date_dmy(data.get("ngay_bat_dau")),
        ngay_ket_thuc=_parse_date_dmy(data.get("ngay_ket_thuc")),
        noi_dung=data.get("noi_dung"),
        ghi_chu=data.get("ghi_chu"),
    ))
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

def _fmt_date_display(val: str) -> str:
    """Chuyển YYYY-MM-DD (từ date input) sang DD/MM/YYYY để lưu vào noi_dung."""
    if not val:
        return val
    try:
        return datetime.strptime(val.strip(), "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return val


def _parse_date(val):
    if not val:
        return None
    try:
        return datetime.strptime(val, "%Y-%m-%d").date()
    except ValueError:
        return None


def _parse_date_dmy(val):
    """Parse dd/mm/yyyy (form input từ browser date picker)"""
    if not val:
        return None
    # Browser date input trả về yyyy-mm-dd
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(val.strip(), fmt).date()
        except ValueError:
            continue
    return None


def change_cccd(db: Session, old_cccd: str, new_cccd: str, ly_do: str, nguoi: str) -> Tuple[bool, str]:
    """
    Chuyển toàn bộ dữ liệu từ old_cccd sang new_cccd trong 1 transaction.
    Gọi bởi super_admin only. Filesystem rename xảy ra SAU khi commit DB.
    """
    old_dt = db.get(DoiTuong, old_cccd)
    if not old_dt:
        return False, "Không tìm thấy hồ sơ"
    if db.get(DoiTuong, new_cccd):
        return False, "CCCD mới đã tồn tại trong hệ thống"

    # 1. Tạo DoiTuong mới — copy toàn bộ field, cập nhật path avatar
    avatar = old_dt.anh_chan_dung
    if avatar:
        avatar = avatar.replace(f"avatars/{old_cccd}/", f"avatars/{new_cccd}/")
    new_dt = DoiTuong(
        cccd=new_cccd,
        ho_ten=old_dt.ho_ten,
        ngay_sinh=old_dt.ngay_sinh,
        gioi_tinh=old_dt.gioi_tinh,
        dia_chi_tinh=old_dt.dia_chi_tinh,
        dia_chi_xa=old_dt.dia_chi_xa,
        anh_chan_dung=avatar,
        phan_loai_nghe_nghiep=old_dt.phan_loai_nghe_nghiep,
        chi_tiet_nghe_nghiep=old_dt.chi_tiet_nghe_nghiep,
        ghi_chu_chung=old_dt.ghi_chu_chung,
        dan_toc=old_dt.dan_toc,
        ton_giao=old_dt.ton_giao,
        que_quan=old_dt.que_quan,
        noi_o_hien_nay=old_dt.noi_o_hien_nay,
        quoc_tich=old_dt.quoc_tich,
        is_draft=old_dt.is_draft,
        nguoi_phu_trach_id=old_dt.nguoi_phu_trach_id,
        created_at=old_dt.created_at,
    )
    db.add(new_dt)
    db.flush()  # đảm bảo new_cccd tồn tại trong DB trước khi chuyển FK

    # 2. Dịch chuyển các bảng satellite
    for model in (LienHe, TaiChinh, PhuongTien, NhanThan, HoSoDacThu, QuaTrinhHoatDong):
        db.execute(sa_update(model).where(model.cccd == old_cccd).values(cccd=new_cccd))

    # 3. TaiLieu: chuyển FK + cập nhật đường dẫn (docs/{old}/ → docs/{new}/)
    db.execute(sa_update(TaiLieu).where(TaiLieu.cccd == old_cccd).values(cccd=new_cccd))
    db.execute(
        sa_update(TaiLieu)
        .where(TaiLieu.cccd == new_cccd, TaiLieu.duong_dan.isnot(None))
        .values(duong_dan=sa_func.replace(TaiLieu.duong_dan, f"/{old_cccd}/", f"/{new_cccd}/"))
    )

    # 4. QuanHeDoiTuong: chuyển 2 chiều cccd_1 và cccd_2
    db.execute(sa_update(QuanHeDoiTuong).where(QuanHeDoiTuong.cccd_1 == old_cccd).values(cccd_1=new_cccd))
    db.execute(sa_update(QuanHeDoiTuong).where(QuanHeDoiTuong.cccd_2 == old_cccd).values(cccd_2=new_cccd))

    # 5. Ghi lịch sử + audit
    db.add(CCCDHistory(
        cccd_cu=old_cccd,
        cccd_moi=new_cccd,
        doi_tuong_cccd_hien_tai=new_cccd,
        ly_do=ly_do or None,
        nguoi_thuc_hien=nguoi,
    ))
    _log(db, "doi_tuong", "CHANGE_CCCD", old_cccd, old_cccd, new_cccd, nguoi)

    # 6. Xóa hồ sơ cũ — tất cả FK đã chuyển sang new_cccd, CASCADE không tác động gì
    db.delete(old_dt)

    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("change_cccd thất bại: %s → %s", old_cccd, new_cccd)
        return False, "Lỗi cơ sở dữ liệu khi đổi CCCD"

    # 7. Đổi tên thư mục files SAU khi DB commit (filesystem không rollback được)
    upload_root = (Path(settings.BASE_DIR) / settings.UPLOAD_DIR).resolve()
    for sub in ("avatars", "docs"):
        old_dir = (upload_root / sub / old_cccd).resolve()
        new_dir = (upload_root / sub / new_cccd).resolve()
        try:
            old_dir.relative_to(upload_root)
            new_dir.relative_to(upload_root)
        except ValueError:
            continue
        if old_dir.exists() and not new_dir.exists():
            old_dir.rename(new_dir)

    return True, new_cccd


def _log(db, bang, hanh_dong, khoa, cu, moi, nguoi):
    """
    F-17 fix: log exception thay vì nuốt im lặng.
    F-18 LƯU Ý: caller phải redact field nhạy cảm trước khi truyền `cu`/`moi`.
    """
    try:
        db.add(AuditLog(bang=bang, hanh_dong=hanh_dong, khoa_chinh=khoa,
                        du_lieu_cu=cu, du_lieu_moi=moi, nguoi_thuc_hien=nguoi))
    except Exception:
        logger.exception("Không ghi được audit log: bang=%s hanh_dong=%s", bang, hanh_dong)
