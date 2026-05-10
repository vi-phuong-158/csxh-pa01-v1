from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from backend.db.base import Base


# ============================================
# Core Person Model
# ============================================
class DoiTuong(Base):
    __tablename__ = "doi_tuong"

    cccd: Mapped[str] = mapped_column(String, primary_key=True)
    ho_ten: Mapped[Optional[str]] = mapped_column(String, index=True)
    ngay_sinh: Mapped[Optional[datetime]] = mapped_column(Date)
    gioi_tinh: Mapped[Optional[str]] = mapped_column(String, index=True)
    dia_chi_tinh: Mapped[Optional[str]] = mapped_column(String, default="Phú Thọ")
    dia_chi_xa: Mapped[Optional[str]] = mapped_column(String, index=True)
    anh_chan_dung: Mapped[Optional[str]] = mapped_column(String)
    phan_loai_nghe_nghiep: Mapped[Optional[str]] = mapped_column(String, index=True)
    chi_tiet_nghe_nghiep: Mapped[Optional[str]] = mapped_column(String)
    ghi_chu_chung: Mapped[Optional[str]] = mapped_column(Text)
    dan_toc: Mapped[Optional[str]] = mapped_column(String)
    ton_giao: Mapped[Optional[str]] = mapped_column(String)
    que_quan: Mapped[Optional[str]] = mapped_column(String)
    noi_o_hien_nay: Mapped[Optional[str]] = mapped_column(String)
    quoc_tich: Mapped[Optional[str]] = mapped_column(String)
    is_draft: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    # F-14: cán bộ phụ trách hồ sơ. NULL = chưa phân công (mọi user xem được).
    # Đã có FK -> users.id; ondelete=SET NULL để khi xoá user, hồ sơ chỉ
    # mất thông tin phụ trách chứ KHÔNG bị xoá theo (an toàn dữ liệu).
    nguoi_phu_trach_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    lien_he: Mapped[List["LienHe"]] = relationship(back_populates="doi_tuong", cascade="all, delete-orphan")
    tai_chinh: Mapped[List["TaiChinh"]] = relationship(back_populates="doi_tuong", cascade="all, delete-orphan")
    phuong_tien: Mapped[List["PhuongTien"]] = relationship(back_populates="doi_tuong", cascade="all, delete-orphan")
    nhan_than: Mapped[List["NhanThan"]] = relationship(back_populates="doi_tuong", cascade="all, delete-orphan")
    ho_so_dac_thu: Mapped[List["HoSoDacThu"]] = relationship(back_populates="doi_tuong", cascade="all, delete-orphan")
    tai_lieu: Mapped[List["TaiLieu"]] = relationship(back_populates="doi_tuong", cascade="all, delete-orphan")
    qua_trinh: Mapped[List["QuaTrinhHoatDong"]] = relationship(back_populates="doi_tuong", cascade="all, delete-orphan")
    quan_he_as_1: Mapped[List["QuanHeDoiTuong"]] = relationship(
        foreign_keys="[QuanHeDoiTuong.cccd_1]", back_populates="doi_tuong_1", cascade="all, delete-orphan",
    )
    quan_he_as_2: Mapped[List["QuanHeDoiTuong"]] = relationship(
        foreign_keys="[QuanHeDoiTuong.cccd_2]", back_populates="doi_tuong_2", cascade="all, delete-orphan",
    )


# ============================================
# Satellite Models
# ============================================
class LienHe(Base):
    __tablename__ = "lien_he"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cccd: Mapped[str] = mapped_column(ForeignKey("doi_tuong.cccd", ondelete="CASCADE"))
    loai_lien_he: Mapped[Optional[str]] = mapped_column(String)
    gia_tri: Mapped[Optional[str]] = mapped_column(String)
    ghi_chu: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    doi_tuong: Mapped["DoiTuong"] = relationship(back_populates="lien_he")


class TaiChinh(Base):
    __tablename__ = "tai_chinh"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cccd: Mapped[str] = mapped_column(ForeignKey("doi_tuong.cccd", ondelete="CASCADE"))
    ngan_hang: Mapped[Optional[str]] = mapped_column(String)
    so_tai_khoan: Mapped[Optional[str]] = mapped_column(String)
    chu_tai_khoan: Mapped[Optional[str]] = mapped_column(String)
    ghi_chu: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    doi_tuong: Mapped["DoiTuong"] = relationship(back_populates="tai_chinh")


class PhuongTien(Base):
    __tablename__ = "phuong_tien"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cccd: Mapped[str] = mapped_column(ForeignKey("doi_tuong.cccd", ondelete="CASCADE"))
    loai_xe: Mapped[Optional[str]] = mapped_column(String)
    bien_kiem_soat: Mapped[Optional[str]] = mapped_column(String)
    ten_phuong_tien: Mapped[Optional[str]] = mapped_column(String)
    ghi_chu: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    doi_tuong: Mapped["DoiTuong"] = relationship(back_populates="phuong_tien")


class NhanThan(Base):
    __tablename__ = "nhan_than"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cccd: Mapped[str] = mapped_column(ForeignKey("doi_tuong.cccd", ondelete="CASCADE"))
    loai_quan_he: Mapped[str] = mapped_column(String)
    ho_ten: Mapped[Optional[str]] = mapped_column(String)
    cccd_nhan_than: Mapped[Optional[str]] = mapped_column(String)
    ngay_sinh: Mapped[Optional[datetime]] = mapped_column(Date)
    gioi_tinh: Mapped[Optional[str]] = mapped_column(String, default="")
    dan_toc: Mapped[Optional[str]] = mapped_column(String)
    ton_giao: Mapped[Optional[str]] = mapped_column(String)
    quoc_tich: Mapped[Optional[str]] = mapped_column(String)
    dia_chi_tinh: Mapped[Optional[str]] = mapped_column(String, default="")
    dia_chi_xa: Mapped[Optional[str]] = mapped_column(String, default="")
    nghe_nghiep: Mapped[Optional[str]] = mapped_column(String)
    noi_o: Mapped[Optional[str]] = mapped_column(Text)
    ghi_chu: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    doi_tuong: Mapped["DoiTuong"] = relationship(back_populates="nhan_than")


class HoSoDacThu(Base):
    __tablename__ = "ho_so_dac_thu"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cccd: Mapped[str] = mapped_column(ForeignKey("doi_tuong.cccd", ondelete="CASCADE"))
    loai_hinh: Mapped[str] = mapped_column(String)
    noi_dung_chi_tiet: Mapped[Optional[str]] = mapped_column(Text)
    ghi_chu: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    doi_tuong: Mapped["DoiTuong"] = relationship(back_populates="ho_so_dac_thu")


class TaiLieu(Base):
    __tablename__ = "tai_lieu"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cccd: Mapped[str] = mapped_column(ForeignKey("doi_tuong.cccd", ondelete="CASCADE"))
    ten_file_goc: Mapped[Optional[str]] = mapped_column(String)
    ten_file_luu: Mapped[Optional[str]] = mapped_column(String)
    duong_dan: Mapped[Optional[str]] = mapped_column(String)
    loai_tai_lieu: Mapped[Optional[str]] = mapped_column(String)
    mo_ta: Mapped[Optional[str]] = mapped_column(Text)
    dung_luong: Mapped[Optional[int]] = mapped_column(Integer)
    dinh_dang: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    doi_tuong: Mapped["DoiTuong"] = relationship(back_populates="tai_lieu")


class QuaTrinhHoatDong(Base):
    __tablename__ = "qua_trinh_hoat_dong"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cccd: Mapped[str] = mapped_column(ForeignKey("doi_tuong.cccd", ondelete="CASCADE"))
    thoi_gian: Mapped[Optional[str]] = mapped_column(String)
    ngay_bat_dau: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True, index=True)
    ngay_ket_thuc: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True, index=True)
    noi_dung: Mapped[Optional[str]] = mapped_column(Text)
    ghi_chu: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    doi_tuong: Mapped["DoiTuong"] = relationship(back_populates="qua_trinh")


# ============================================
# System Models
# ============================================
class NguonDuLieu(Base):
    __tablename__ = "nguon_du_lieu"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ten_nguon: Mapped[str] = mapped_column(String)
    loai_nguon: Mapped[Optional[str]] = mapped_column(String)
    thoi_gian_import: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    nguoi_import: Mapped[Optional[str]] = mapped_column(String)
    file_goc: Mapped[Optional[str]] = mapped_column(String)
    ghi_chu: Mapped[Optional[str]] = mapped_column(Text)


class QuanHeDoiTuong(Base):
    __tablename__ = "quan_he_doi_tuong"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cccd_1: Mapped[str] = mapped_column(ForeignKey("doi_tuong.cccd", ondelete="CASCADE"))
    cccd_2: Mapped[str] = mapped_column(ForeignKey("doi_tuong.cccd", ondelete="CASCADE"))
    loai_quan_he: Mapped[Optional[str]] = mapped_column(String)
    mo_ta: Mapped[Optional[str]] = mapped_column(Text)
    nguon_id: Mapped[Optional[int]] = mapped_column(ForeignKey("nguon_du_lieu.id"))
    do_tin_cay: Mapped[Optional[int]] = mapped_column(Integer, default=50)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    doi_tuong_1: Mapped["DoiTuong"] = relationship(foreign_keys=[cccd_1], back_populates="quan_he_as_1")
    doi_tuong_2: Mapped["DoiTuong"] = relationship(foreign_keys=[cccd_2], back_populates="quan_he_as_2")


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bang: Mapped[str] = mapped_column(String)
    hanh_dong: Mapped[str] = mapped_column(String)
    khoa_chinh: Mapped[Optional[str]] = mapped_column(String)
    du_lieu_cu: Mapped[Optional[str]] = mapped_column(Text)
    du_lieu_moi: Mapped[Optional[str]] = mapped_column(Text)
    nguoi_thuc_hien: Mapped[Optional[str]] = mapped_column(String)
    ip_address: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class CCCDHistory(Base):
    """Lưu lịch sử đổi số CCCD để tra cứu CCCD cũ."""
    __tablename__ = "cccd_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cccd_cu: Mapped[str] = mapped_column(String, index=True)
    cccd_moi: Mapped[str] = mapped_column(String, index=True)
    doi_tuong_cccd_hien_tai: Mapped[Optional[str]] = mapped_column(
        ForeignKey("doi_tuong.cccd", ondelete="SET NULL"), nullable=True
    )
    ly_do: Mapped[Optional[str]] = mapped_column(Text)
    nguoi_thuc_hien: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    password_hash: Mapped[str] = mapped_column(String)
    ho_ten: Mapped[Optional[str]] = mapped_column(String)
    role: Mapped[Optional[str]] = mapped_column(String, default="user")
    is_active: Mapped[int] = mapped_column(Integer, default=1)
    must_change_password: Mapped[int] = mapped_column(Integer, default=0)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    lockout_until: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime)
