# -*- coding: utf-8 -*-
import streamlit as st
import json
import logging
from datetime import datetime, date

from constants import (
    GIOI_TINH_OPTIONS, TINH_OPTIONS, DANH_SACH_XA_PHU_THO,
    PHAN_LOAI_NGHE_NGHIEP_OPTIONS, LOAI_LIEN_HE_OPTIONS,
    DANH_SACH_NGAN_HANG, LOAI_XE_OPTIONS, LOAI_HINH_DAC_THU,
    DANH_SACH_QUOC_GIA, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB,
    LOAI_TAI_LIEU_OPTIONS, Messages
)
from services import (
    check_cccd_exists, save_doi_tuong, save_lien_he,
    save_tai_chinh, save_phuong_tien, save_nhan_than,
    save_ho_so_dac_thu, save_tai_lieu
)
from database import (
    get_qua_trinh_hoat_dong, delete_qua_trinh_hoat_dong,
    save_qua_trinh_hoat_dong
)
from views.profile import (
    get_doi_tuong_detail, get_nhan_than_by_cccd, get_lien_he_by_cccd,
    get_tai_chinh_by_cccd, get_phuong_tien_by_cccd,
    get_ho_so_dac_thu_by_cccd, get_tai_lieu_by_cccd,
    get_file_path, delete_nhan_than, delete_lien_he,
    delete_tai_chinh, delete_phuong_tien, delete_ho_so_dac_thu,
    delete_tai_lieu, update_doi_tuong
)
from utils.text_utils import format_date_vn
from utils.ui_components import render_address_fields
from .utils import validate_cccd_for_action

logger = logging.getLogger(__name__)

# ===================================================================
# Helper: khởi tạo staging state
# ===================================================================
def _init_staging():
    """Khởi tạo các key staging trong session_state nếu chưa có."""
    defaults = {
        "nl_staging_nhan_than": [],   # list[dict]
        "nl_staging_qt": [],           # list[dict]
        "nl_staging_lien_he": [],      # list[dict]
        "nl_staging_tai_chinh": [],    # list[dict]
        "nl_staging_phuong_tien": [],  # list[dict]
        "nl_staging_dac_thu": [],      # list[dict]  {loai_hinh, noi_dung, ghi_chu}
        "nl_staging_tai_lieu": [],     # list[dict]  {file, loai, mo_ta}
        "nl_them_bo_sung": False,      # True khi CCCD đã có → chỉ thêm satellite
        "nl_edit_mode": False,          # True khi đang sửa hồ sơ đã có
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _reset_form():
    """Xoá toàn bộ staging và reset form."""
    staging_keys = [
        "nl_staging_nhan_than", "nl_staging_qt", "nl_staging_lien_he",
        "nl_staging_tai_chinh", "nl_staging_phuong_tien",
        "nl_staging_dac_thu", "nl_staging_tai_lieu", "nl_them_bo_sung",
        "nl_cccd", "nl_ho_ten", "nl_edit_mode",
    ]
    for k in staging_keys:
        if k in st.session_state:
            del st.session_state[k]
    st.session_state.current_cccd = None


# ===================================================================
# Helper: preview staging list trong từng tab
# ===================================================================
def _render_staging_list(key: str, label_fn, empty_msg: str):
    """
    Hiển thị danh sách items đang chờ lưu từ staging.
    label_fn(item) -> str nhãn hiển thị cho mỗi item.
    Trả về True nếu list không rỗng.
    """
    items = st.session_state.get(key, [])
    if not items:
        return False
    st.markdown(f"**📋 Danh sách chờ lưu ({len(items)} mục):**")
    for i, item in enumerate(items):
        col_info, col_del = st.columns([5, 1])
        with col_info:
            st.markdown(f"↳ {label_fn(item)}")
        with col_del:
            if st.button("🗑️", key=f"del_{key}_{i}"):
                st.session_state[key].pop(i)
                st.rerun()
    return True


# ===================================================================
# Main page
# ===================================================================
def page_nhap_lieu():
    """Trang Nhập liệu - Form thêm mới / bổ sung hồ sơ đối tượng"""
    _init_staging()

    st.markdown("# 📝 Nhập liệu")
    st.markdown("### Thêm mới / bổ sung hồ sơ đối tượng")

    # ------------------------------------------------------------------
    # Banner hướng dẫn
    # ------------------------------------------------------------------
    st.info(
        "💡 **Hướng dẫn:** Nhập thông tin tự do ở tất cả các tab, "
        "sau đó nhấn **✅ Lưu toàn bộ hồ sơ** một lần ở cuối trang.",
        icon=None
    )
    st.markdown("---")

    # Tabs cho các phần nhập liệu
    tab1, tab_nhan_than, tab_qt, tab2, tab3, tab_tai_lieu = st.tabs([
        "👤 Thông tin cá nhân",
        "👨‍👩‍👧‍👦 Thân nhân",
        "⏳ Quá trình hoạt động",
        "📞 Liên hệ & Tài sản",
        "🌐 Yếu tố nước ngoài",
        "📎 Tài liệu đính kèm"
    ])

    # ==================================================================
    # TAB 1 – THÔNG TIN CÁ NHÂN
    # ==================================================================
    with tab1:
        st.markdown("#### 📋 Thông tin cơ bản")
        st.caption("🔑 CCCD và Họ tên là bắt buộc để lưu hồ sơ.")

        col1, col2 = st.columns(2)

        with col1:
            cccd = st.text_input(
                "Số CCCD *",
                placeholder="Nhập 12 số CCCD",
                max_chars=12,
                key="nl_cccd"
            )

            # Cảnh báo khi CCCD đã tồn tại → hỏi muốn sửa không
            existing_data = None
            if cccd and len(cccd) == 12:
                if check_cccd_exists(cccd):
                    existing_data = get_doi_tuong_detail(cccd)
                    if not st.session_state.get("nl_edit_mode"):
                        st.warning(
                            f"⚠️ CCCD **{cccd}** đã có trong hệ thống."
                        )
                        col_edit, col_bosung = st.columns(2)
                        with col_edit:
                            if st.button("✏️ Sửa thông tin cá nhân", key="btn_edit_existing", type="primary", use_container_width=True):
                                # Load dữ liệu cũ vào session_state → form auto-fill
                                if existing_data:
                                    st.session_state["nl_ho_ten"] = existing_data.get("ho_ten", "")
                                    # Ngày sinh
                                    ns = existing_data.get("ngay_sinh")
                                    if ns:
                                        try:
                                            st.session_state["main_ngay_sinh"] = datetime.strptime(str(ns), "%Y-%m-%d").date()
                                        except (ValueError, TypeError):
                                            pass
                                    # Giới tính
                                    gt = existing_data.get("gioi_tinh", "")
                                    if gt in GIOI_TINH_OPTIONS:
                                        st.session_state["main_gioi_tinh"] = gt
                                    # Tỉnh
                                    tinh = existing_data.get("dia_chi_tinh", "Phú Thọ")
                                    if tinh in TINH_OPTIONS:
                                        st.session_state["main_dia_chi_tinh"] = tinh
                                    # Xã
                                    xa = existing_data.get("dia_chi_xa", "")
                                    if tinh == "Phú Thọ":
                                        xa_options = ["-- Chọn xã/phường --"] + DANH_SACH_XA_PHU_THO
                                        if xa in xa_options:
                                            st.session_state["xa_phuong_select"] = xa
                                    else:
                                        st.session_state["main_dia_chi_xa_text"] = xa
                                        st.session_state["main_dia_chi_chi_tiet"] = existing_data.get("dia_chi_chi_tiet", "")
                                    # Nghề nghiệp
                                    pl = existing_data.get("phan_loai_nghe_nghiep", "")
                                    if pl in PHAN_LOAI_NGHE_NGHIEP_OPTIONS:
                                        st.session_state["main_phan_loai_nghe"] = pl
                                    st.session_state["main_chi_tiet_nghe"] = existing_data.get("chi_tiet_nghe_nghiep", "")
                                    st.session_state["main_ghi_chu"] = existing_data.get("ghi_chu_chung", "")

                                st.session_state.nl_edit_mode = True
                                st.session_state.nl_them_bo_sung = True
                                st.rerun()
                        with col_bosung:
                            if st.button("📎 Chỉ bổ sung thân nhân/liên hệ", key="btn_bosung_only", use_container_width=True):
                                st.session_state.nl_them_bo_sung = True
                                st.session_state.nl_edit_mode = False
                                st.rerun()
                    else:
                        st.info(
                            "📝 **Chế độ chỉnh sửa** — Thay đổi thông tin và nhấn **Lưu toàn bộ** ở cuối trang."
                        )
                        st.session_state.nl_them_bo_sung = True
                else:
                    st.session_state.nl_them_bo_sung = False
                    st.session_state.nl_edit_mode = False

            ho_ten = st.text_input(
                "Họ và tên *",
                placeholder="Nguyễn Văn A",
                key="nl_ho_ten"
            )

            # Avatar Upload
            st.markdown("##### 📸 Ảnh đại diện")
            avatar_file = st.file_uploader(
                "Tải lên ảnh chân dung", type=['png', 'jpg', 'jpeg'],
                key="main_avatar_uploader"
            )

            ngay_sinh = st.date_input(
                "Ngày sinh",
                value=None,
                min_value=date(1900, 1, 1),
                max_value=datetime.now().date(),
                format="DD/MM/YYYY",
                key="main_ngay_sinh"
            )

            gioi_tinh = st.selectbox(
                "Giới tính",
                GIOI_TINH_OPTIONS,
                key="main_gioi_tinh"
            )

        with col2:
            dia_chi_tinh, dia_chi_xa, dia_chi_chi_tiet = render_address_fields(
                prefix="main",
                default_tinh="Phú Thọ",
                default_xa="",
                default_chi_tiet=""
            )

            phan_loai = st.selectbox(
                "Phân loại nghề nghiệp",
                PHAN_LOAI_NGHE_NGHIEP_OPTIONS,
                key="main_phan_loai_nghe"
            )

            chi_tiet_nghe = st.text_input(
                "Chi tiết nơi làm việc",
                placeholder="Ví dụ: Công an tỉnh Phú Thọ",
                key="main_chi_tiet_nghe"
            )

        st.markdown("---")
        ghi_chu = st.text_area(
            "Ghi chú chung",
            placeholder="Các thông tin ghi chú khác...",
            height=100,
            key="main_ghi_chu"
        )



    # ==================================================================
    # TAB THÂN NHÂN
    # ==================================================================
    with tab_nhan_than:
        st.markdown("#### 👨‍👩‍👧‍👦 Thông tin thân nhân")

        # Hiển thị danh sách đã có trong DB (nếu CCCD đã tồn tại)
        cccd_now = st.session_state.get("nl_cccd", "")
        if cccd_now and len(cccd_now) == 12 and check_cccd_exists(cccd_now):
            df_nt_db = get_nhan_than_by_cccd(cccd_now)
            if not df_nt_db.empty:
                with st.expander(f"📂 Đã có trong hệ thống ({len(df_nt_db)} thân nhân)", expanded=False):
                    for _, row in df_nt_db.iterrows():
                        col_info, col_del = st.columns([5, 1])
                        with col_info:
                            st.markdown(
                                f"**{row['loai_quan_he']}**: {row['ho_ten']} | "
                                f"📅 {format_date_vn(row['ngay_sinh']) if row.get('ngay_sinh') else 'N/A'} | "
                                f"💼 {row['nghe_nghiep'] or 'N/A'}"
                            )
                        with col_del:
                            with st.popover("🗑️"):
                                st.markdown(f"Bạn có chắc muốn xóa **{row['ho_ten']}**?")
                                if st.button("Xác nhận xóa", key=f"del_nt_db_{row['id']}", type="primary"):
                                    delete_nhan_than(row['id'])
                                    st.toast(f"✅ Đã xóa {row['loai_quan_he']}: {row['ho_ten']}")
                                    st.rerun()

        st.markdown("---")

        # Preview staging
        _render_staging_list(
            "nl_staging_nhan_than",
            lambda x: f"**{x['loai_quan_he']}**: {x['ho_ten']} | {x['nghe_nghiep'] or ''}",
            "Chưa có thân nhân nào trong danh sách chờ."
        )

        st.markdown("##### ➕ Thêm thân nhân mới")

        loai_quan_he = st.selectbox(
            "Loại quan hệ",
            ["Bố đẻ", "Mẹ đẻ", "Vợ/Chồng", "Anh/Chị em ruột", "Anh/Chị em họ",
             "Ông/Bà", "Con", "Bạn thân", "Đồng nghiệp", "Khác"],
            key="nt_loai_quan_he"
        )

        col1, col2 = st.columns(2)
        with col1:
            nt_ho_ten = st.text_input("Họ và tên *", placeholder="Nguyễn Văn A", key="nt_ho_ten")
            nt_cccd = st.text_input("Số CCCD", placeholder="Nhập 12 số CCCD (nếu có)", key="nt_cccd")

            # Auto-fill khi cccd_nhan_than trùng trong DB
            if nt_cccd and len(nt_cccd) == 12 and nt_cccd.isdigit():
                nt_existing = get_doi_tuong_detail(nt_cccd)
                if nt_existing:
                    st.info(f"📋 Tìm thấy hồ sơ: **{nt_existing.get('ho_ten', '')}** — Nhấn nút bên dưới để tự động điền.")
                    def do_autofill_nt():
                        st.session_state["nt_ho_ten"] = nt_existing.get("ho_ten", "")
                        ns = nt_existing.get("ngay_sinh")
                        if ns:
                            try:
                                st.session_state["nt_ngay_sinh"] = datetime.strptime(str(ns), "%Y-%m-%d").date()
                            except (ValueError, TypeError):
                                pass
                        gt = nt_existing.get("gioi_tinh", "")
                        if gt in GIOI_TINH_OPTIONS:
                            st.session_state["nt_gioi_tinh"] = gt
                        tinh = nt_existing.get("dia_chi_tinh", "Phú Thọ")
                        if tinh in TINH_OPTIONS:
                            st.session_state["nt_dia_chi_tinh"] = tinh
                        xa = nt_existing.get("dia_chi_xa", "")
                        if tinh == "Phú Thọ":
                            xa_opts = ["-- Chọn xã/phường --"] + DANH_SACH_XA_PHU_THO
                            if xa in xa_opts:
                                st.session_state["nt_xa_phuong_select"] = xa
                        else:
                            st.session_state["nt_dia_chi_xa_text"] = xa
                        st.session_state["nt_dia_chi_chi_tiet"] = nt_existing.get("dia_chi_chi_tiet", "")
                        pl = nt_existing.get("phan_loai_nghe_nghiep", "")
                        if pl in PHAN_LOAI_NGHE_NGHIEP_OPTIONS:
                            st.session_state["nt_phan_loai_nghe"] = pl
                        st.session_state["nt_nghe_nghiep"] = nt_existing.get("chi_tiet_nghe_nghiep", "")
                        
                    st.button("✅ Tự động điền thông tin", key="btn_autofill_nt", type="primary", on_click=do_autofill_nt)
                else:
                    st.caption(f"ℹ️ CCCD {nt_cccd} chưa có trong hệ thống — sẽ tự tạo hồ sơ mới khi lưu.")
            nt_ngay_sinh = st.date_input(
                "Ngày sinh", value=None, key="nt_ngay_sinh", format="DD/MM/YYYY",
                min_value=date(1900, 1, 1), max_value=date(2100, 12, 31)
            )
            nt_gioi_tinh = st.selectbox("Giới tính", GIOI_TINH_OPTIONS, key="nt_gioi_tinh")

        with col2:
            nt_dia_chi_tinh, nt_dia_chi_xa, nt_dia_chi_chi_tiet = render_address_fields(
                prefix="nt",
                default_tinh="Phú Thọ",
                default_xa="",
                default_chi_tiet=""
            )
            
            nt_phan_loai_nghe = st.selectbox("Phân loại nghề nghiệp", PHAN_LOAI_NGHE_NGHIEP_OPTIONS, key="nt_phan_loai_nghe")
            nt_nghe_nghiep = st.text_input("Chi tiết nghề nghiệp", placeholder="Giáo viên THPT...", key="nt_nghe_nghiep")
            nt_noi_o = st.text_input("Nơi ở hiện nay", placeholder="Địa chỉ hiện tại", key="nt_noi_o")

        nt_ghi_chu = st.text_input("Ghi chú", placeholder="Ghi chú thêm...", key="nt_ghi_chu")

        if st.button("➕ Thêm vào danh sách", key="btn_add_nhan_than", use_container_width=True):
            if nt_ho_ten:
                nghe_nghiep_full = f"{nt_phan_loai_nghe}: {nt_nghe_nghiep}" if nt_nghe_nghiep else nt_phan_loai_nghe
                st.session_state.nl_staging_nhan_than.append({
                    "loai_quan_he": loai_quan_he,
                    "ho_ten": nt_ho_ten,
                    "cccd_nhan_than": nt_cccd,
                    "ngay_sinh": nt_ngay_sinh.strftime('%Y-%m-%d') if nt_ngay_sinh else None,
                    "gioi_tinh": nt_gioi_tinh,
                    "dia_chi_tinh": nt_dia_chi_tinh,
                    "dia_chi_xa": nt_dia_chi_xa,
                    "dia_chi_chi_tiet": nt_dia_chi_chi_tiet,
                    "nghe_nghiep": nghe_nghiep_full,
                    "noi_o": nt_noi_o,
                    "ghi_chu": nt_ghi_chu,
                })
                st.toast(f"✅ Đã thêm {loai_quan_he}: {nt_ho_ten} vào danh sách chờ", icon="📋")
                st.rerun()
            else:
                st.warning("⚠️ Vui lòng nhập họ tên thân nhân!")

    # ==================================================================
    # TAB QUÁ TRÌNH HOẠT ĐỘNG
    # ==================================================================
    with tab_qt:
        st.markdown("#### ⏳ Quá trình hoạt động (Lịch sử nhân thân)")

        # Hiển thị dữ liệu đã có trong DB
        cccd_now = st.session_state.get("nl_cccd", "")
        if cccd_now and len(cccd_now) == 12 and check_cccd_exists(cccd_now):
            qt_list_db = get_qua_trinh_hoat_dong(cccd_now)
            if qt_list_db:
                with st.expander(f"📂 Đã có trong hệ thống ({len(qt_list_db)} mục)", expanded=False):
                    for item in qt_list_db:
                        col_info, col_del = st.columns([5, 1])
                        with col_info:
                            st.markdown(f"**{format_date_vn(item['thoi_gian'])}**: {item['noi_dung']}")
                        with col_del:
                            with st.popover("🗑️"):
                                st.markdown(f"Xóa hoạt động: **{item['thoi_gian']}**?")
                                if st.button("Xác nhận", key=f"del_qt_db_{item['id']}", type="primary"):
                                    delete_qua_trinh_hoat_dong(item['id'])
                                    st.rerun()

        st.markdown("---")

        # Preview staging
        _render_staging_list(
            "nl_staging_qt",
            lambda x: f"**{format_date_vn(x['thoi_gian'])}**: {x['noi_dung']}",
            ""
        )

        st.markdown("##### ➕ Thêm quá trình hoạt động")

        col_qt_time, col_qt_content = st.columns([1, 2])
        with col_qt_time:
            c1, c2 = st.columns(2)
            with c1:
                qt_tu_nam = st.text_input("Từ năm", placeholder="2010", key="qt_tu_nam")
            with c2:
                qt_den_nam = st.text_input("Đến năm", placeholder="2015", key="qt_den_nam")
        with col_qt_content:
            qt_noi_dung = st.text_area(
                "Nội dung hoạt động", placeholder="Mô tả hoạt động...",
                height=100, key="qt_noi_dung"
            )

        qt_ghi_chu = st.text_input("Ghi chú", placeholder="Ghi chú thêm...", key="qt_ghi_chu")

        if st.button("➕ Thêm vào danh sách", key="btn_add_qt", use_container_width=True):
            if qt_noi_dung:
                if qt_tu_nam and qt_den_nam:
                    qt_thoi_gian = f"{qt_tu_nam} - {qt_den_nam}"
                elif qt_tu_nam:
                    qt_thoi_gian = f"Từ {qt_tu_nam}"
                elif qt_den_nam:
                    qt_thoi_gian = f"Đến {qt_den_nam}"
                else:
                    qt_thoi_gian = "Không xác định"

                st.session_state.nl_staging_qt.append({
                    "thoi_gian": qt_thoi_gian,
                    "noi_dung": qt_noi_dung,
                    "ghi_chu": qt_ghi_chu,
                })
                st.toast("✅ Đã thêm quá trình vào danh sách chờ", icon="📋")
                st.rerun()
            else:
                st.warning("⚠️ Vui lòng nhập nội dung hoạt động!")

    # ==================================================================
    # TAB LIÊN HỆ & TÀI SẢN
    # ==================================================================
    with tab2:
        st.markdown("#### 📞 Thông tin liên hệ & Tài sản")

        cccd_now = st.session_state.get("nl_cccd", "")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### 📱 Số điện thoại / Mạng xã hội")

            # Dữ liệu đã có trong DB
            if cccd_now and len(cccd_now) == 12 and check_cccd_exists(cccd_now):
                df_lh_db = get_lien_he_by_cccd(cccd_now)
                if not df_lh_db.empty:
                    with st.expander(f"📂 Đã có trong hệ thống ({len(df_lh_db)})", expanded=False):
                        for _, row in df_lh_db.iterrows():
                            col_i, col_d = st.columns([4, 1])
                            with col_i:
                                st.text(f"- {row['loai_lien_he']}: {row['gia_tri']}")
                            with col_d:
                                with st.popover("🗑️"):
                                    if st.button("Xóa", key=f"del_lh_db_{row['id']}", type="primary"):
                                        delete_lien_he(row['id'])
                                        st.rerun()

            # Preview staging
            _render_staging_list(
                "nl_staging_lien_he",
                lambda x: f"**{x['loai']}**: {x['gia_tri']}",
                ""
            )

            loai_lien_he = st.selectbox("Loại liên hệ", LOAI_LIEN_HE_OPTIONS, key="lh_loai")
            gia_tri_lien_he = st.text_input(
                "Giá trị", placeholder="0912345678 hoặc link FB/Zalo...", key="lien_he_value"
            )
            ghi_chu_lien_he = st.text_input("Ghi chú", key="lien_he_note", placeholder="Ghi chú thêm...")

            if st.button("➕ Thêm liên hệ", use_container_width=True, key="btn_add_lh"):
                if gia_tri_lien_he:
                    st.session_state.nl_staging_lien_he.append({
                        "loai": loai_lien_he,
                        "gia_tri": gia_tri_lien_he,
                        "ghi_chu": ghi_chu_lien_he,
                    })
                    st.toast(f"✅ Đã thêm {loai_lien_he}: {gia_tri_lien_he}", icon="📋")
                    st.rerun()
                else:
                    st.warning("⚠️ Vui lòng nhập giá trị liên hệ!")

        with col2:
            st.markdown("##### 🏦 Tài khoản ngân hàng")

            if cccd_now and len(cccd_now) == 12 and check_cccd_exists(cccd_now):
                df_tc_db = get_tai_chinh_by_cccd(cccd_now)
                if not df_tc_db.empty:
                    with st.expander(f"📂 Đã có trong hệ thống ({len(df_tc_db)})", expanded=False):
                        for _, row in df_tc_db.iterrows():
                            col_i, col_d = st.columns([4, 1])
                            with col_i:
                                st.text(f"- {row['ngan_hang']}: {row['so_tai_khoan']}")
                            with col_d:
                                with st.popover("🗑️"):
                                    if st.button("Xóa", key=f"del_tc_db_{row['id']}", type="primary"):
                                        delete_tai_chinh(row['id'])
                                        st.rerun()

            # Preview staging
            _render_staging_list(
                "nl_staging_tai_chinh",
                lambda x: f"**{x['ngan_hang']}**: {x['so_tai_khoan']}",
                ""
            )

            ngan_hang = st.selectbox("Ngân hàng", DANH_SACH_NGAN_HANG, key="ngan_hang_tab2")
            so_tai_khoan = st.text_input("Số tài khoản", placeholder="1234567890", key="stk_tab2")
            chu_tai_khoan = st.text_input("Chủ tài khoản", placeholder="NGUYEN VAN A", key="ctk_tab2")

            if st.button("➕ Thêm tài khoản", use_container_width=True, key="btn_add_tc"):
                if so_tai_khoan:
                    st.session_state.nl_staging_tai_chinh.append({
                        "ngan_hang": ngan_hang,
                        "so_tai_khoan": so_tai_khoan,
                        "chu_tai_khoan": chu_tai_khoan,
                    })
                    st.toast(f"✅ Đã thêm TK {ngan_hang}: {so_tai_khoan}", icon="📋")
                    st.rerun()
                else:
                    st.warning("⚠️ Vui lòng nhập số tài khoản!")

        st.markdown("---")
        st.markdown("##### 🚗 Phương tiện giao thông")

        if cccd_now and len(cccd_now) == 12 and check_cccd_exists(cccd_now):
            df_pt_db = get_phuong_tien_by_cccd(cccd_now)
            if not df_pt_db.empty:
                with st.expander(f"📂 Đã có trong hệ thống ({len(df_pt_db)})", expanded=False):
                    for _, row in df_pt_db.iterrows():
                        col_i, col_d = st.columns([4, 1])
                        with col_i:
                            st.text(f"- {row['loai_xe']}: {row['bien_kiem_soat']}")
                        with col_d:
                            with st.popover("🗑️"):
                                if st.button("Xóa", key=f"del_pt_db_{row['id']}", type="primary"):
                                    delete_phuong_tien(row['id'])
                                    st.rerun()

        # Preview staging
        _render_staging_list(
            "nl_staging_phuong_tien",
            lambda x: f"**{x['loai_xe']}**: {x['bien_so']} — {x['ten_xe']}",
            ""
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            loai_xe = st.selectbox("Loại xe", LOAI_XE_OPTIONS, key="loai_xe_tab2")
        with col2:
            bien_so = st.text_input("Biển kiểm soát", placeholder="19A-12345", key="bien_so_tab2")
        with col3:
            ten_xe = st.text_input("Tên xe", placeholder="Honda Vision...", key="ten_xe_tab2")

        if st.button("➕ Thêm phương tiện", use_container_width=True, key="btn_add_pt"):
            if bien_so:
                st.session_state.nl_staging_phuong_tien.append({
                    "loai_xe": loai_xe,
                    "bien_so": bien_so,
                    "ten_xe": ten_xe,
                })
                st.toast(f"✅ Đã thêm xe {loai_xe}: {bien_so}", icon="📋")
                st.rerun()
            else:
                st.warning("⚠️ Vui lòng nhập biển kiểm soát!")

    # ==================================================================
    # TAB YẾU TỐ NƯỚC NGOÀI
    # ==================================================================
    with tab3:
        st.markdown("#### 🌐 Yếu tố nước ngoài & Nghiệp vụ")

        cccd_now = st.session_state.get("nl_cccd", "")

        # Hiển thị dữ liệu đã có
        if cccd_now and len(cccd_now) == 12 and check_cccd_exists(cccd_now):
            df_dt_db = get_ho_so_dac_thu_by_cccd(cccd_now)
            if not df_dt_db.empty:
                with st.expander(f"📂 Đã có trong hệ thống ({len(df_dt_db)} hồ sơ)", expanded=False):
                    for _, row in df_dt_db.iterrows():
                        loai_text = LOAI_HINH_DAC_THU.get(row['loai_hinh'], row['loai_hinh'])
                        col_i, col_d = st.columns([5, 1])
                        with col_i:
                            try:
                                nd = json.loads(row['noi_dung_chi_tiet']) if row['noi_dung_chi_tiet'] else {}
                                preview = " | ".join([str(v) for v in list(nd.values())[:2] if v])
                            except Exception:
                                preview = ""
                            st.markdown(f"**📌 {loai_text}**: {preview}")
                        with col_d:
                            with st.popover("🗑️"):
                                if st.button("Xóa", key=f"del_dt_db_{row['id']}", type="primary"):
                                    delete_ho_so_dac_thu(row['id'])
                                    st.rerun()

        st.markdown("---")

        # Preview staging
        _render_staging_list(
            "nl_staging_dac_thu",
            lambda x: f"**📌 {LOAI_HINH_DAC_THU.get(x['loai_hinh'], x['loai_hinh'])}**",
            ""
        )

        loai_hinh = st.selectbox(
            "Loại hình hồ sơ đặc thù",
            options=list(LOAI_HINH_DAC_THU.keys()),
            format_func=lambda x: f"📌 {LOAI_HINH_DAC_THU[x]}",
            key="dt_loai_hinh"
        )

        st.markdown("---")

        noi_dung_dict = {}

        if loai_hinh == "Hon_Nhan_NN":
            st.markdown("##### 💑 Thông tin đối tác nước ngoài")
            col1, col2 = st.columns(2)
            with col1:
                noi_dung_dict["ten_doi_tac"] = st.text_input("Họ tên đối tác", key="hn_ten")
                noi_dung_dict["quoc_tich"] = st.selectbox("Quốc tịch", DANH_SACH_QUOC_GIA, key="hn_qt")
            with col2:
                noi_dung_dict["so_ho_chieu"] = st.text_input("Số hộ chiếu", key="hn_hc")
                noi_dung_dict["tinh_trang"] = st.selectbox(
                    "Tình trạng",
                    ["Kết hôn hợp pháp", "Sinh sống như vợ chồng", "Đã ly hôn", "Đã qua đời"],
                    key="hn_tt"
                )

        elif loai_hinh == "Lam_Viec_NN":
            st.markdown("##### 🏢 Thông tin tổ chức nước ngoài")
            noi_dung_dict["ten_to_chuc"] = st.text_input("Tên tổ chức NGO/FDI", key="lv_tc")
            col1, col2 = st.columns(2)
            with col1:
                noi_dung_dict["chuc_vu"] = st.text_input("Chức vụ", key="lv_cv")
            with col2:
                noi_dung_dict["thoi_gian"] = st.text_input("Thời gian làm việc", key="lv_tg")
            noi_dung_dict["dia_diem"] = st.text_input("Địa điểm làm việc", key="lv_dd")

        elif loai_hinh == "Hoc_Tap_Cong_Tac_NN":
            st.markdown("##### 🎓 Thông tin du học/công tác nước ngoài")
            col1, col2 = st.columns(2)
            with col1:
                noi_dung_dict["dien_di"] = st.selectbox(
                    "Diện đi",
                    ["Du học tự túc", "Du học ngân sách", "Công tác", "Xuất khẩu lao động", "Khác"],
                    key="ht_dien"
                )
                noi_dung_dict["quoc_gia"] = st.selectbox("Quốc gia", DANH_SACH_QUOC_GIA, key="ht_qg")
            with col2:
                noi_dung_dict["thoi_gian_di"] = st.text_input("Thời gian đi", key="ht_tgd")
                noi_dung_dict["thoi_gian_ve"] = st.text_input("Thời gian về", key="ht_tgv")
            noi_dung_dict["nghe_sau_ve"] = st.text_input("Nghề nghiệp sau khi về", key="ht_nghe")

        elif loai_hinh == "Vi_Pham_NN":
            st.markdown("##### ⚠️ Vi phạm pháp luật ở nước ngoài")
            col1, col2 = st.columns(2)
            with col1:
                noi_dung_dict["quoc_gia"] = st.selectbox("Quốc gia", DANH_SACH_QUOC_GIA, key="vp_qg")
                noi_dung_dict["co_quan_bat"] = st.text_input("Cơ quan bắt giữ", key="vp_cq")
            with col2:
                vp_ngay = st.date_input("Ngày vi phạm", value=None, format="DD/MM/YYYY", key="vp_tg")
                noi_dung_dict["thoi_gian"] = vp_ngay.strftime("%d/%m/%Y") if vp_ngay else ""
                noi_dung_dict["hinh_thuc_xu_ly"] = st.text_input("Hình thức xử lý", key="vp_ht")
            noi_dung_dict["noi_dung_vp"] = st.text_area("Nội dung vi phạm", key="vp_nd", height=100)

        elif loai_hinh == "Xac_Minh":
            st.markdown("##### 🔍 Thông tin xác minh")
            col1, col2 = st.columns(2)
            with col1:
                noi_dung_dict["co_quan_xm"] = st.text_input("Cơ quan xác minh", key="xm_cq")
                xm_ngay = st.date_input("Ngày xác minh", value=None, format="DD/MM/YYYY", key="xm_tg")
                noi_dung_dict["thoi_gian"] = xm_ngay.strftime("%d/%m/%Y") if xm_ngay else ""
            with col2:
                noi_dung_dict["ket_qua"] = st.selectbox(
                    "Kết quả",
                    ["Đủ điều kiện", "Không đủ điều kiện", "Đang xác minh", "Khác"],
                    key="xm_kq"
                )
            noi_dung_dict["noi_dung_xm"] = st.text_area("Nội dung xác minh", key="xm_nd", height=100)

        ghi_chu_dac_thu = st.text_area(
            "Ghi chú thêm", placeholder="Ghi chú về hồ sơ đặc thù...", height=80, key="dt_ghi_chu"
        )

        if st.button("➕ Thêm hồ sơ đặc thù", use_container_width=True, key="btn_add_dt"):
            if any(noi_dung_dict.values()):
                st.session_state.nl_staging_dac_thu.append({
                    "loai_hinh": loai_hinh,
                    "noi_dung": noi_dung_dict.copy(),
                    "ghi_chu": ghi_chu_dac_thu,
                })
                st.toast(f"✅ Đã thêm {LOAI_HINH_DAC_THU[loai_hinh]} vào danh sách chờ", icon="📋")
                st.rerun()
            else:
                st.warning("⚠️ Vui lòng nhập ít nhất một thông tin!")

    # ==================================================================
    # TAB TÀI LIỆU ĐÍNH KÈM
    # ==================================================================
    with tab_tai_lieu:
        st.markdown("#### 📎 Tài liệu đính kèm")

        cccd_now = st.session_state.get("nl_cccd", "")

        # Hiển thị tài liệu đã có trong DB
        if cccd_now and len(cccd_now) == 12 and check_cccd_exists(cccd_now):
            df_tl_db = get_tai_lieu_by_cccd(cccd_now)
            if not df_tl_db.empty:
                with st.expander(f"📂 Đã có trong hệ thống ({len(df_tl_db)} file)", expanded=False):
                    for _, row in df_tl_db.iterrows():
                        col_info, col_dl, col_del = st.columns([4, 1, 1])
                        with col_info:
                            kb = row['dung_luong'] / 1024
                            st.markdown(
                                f"**{row['loai_tai_lieu']}**: {row['ten_file_goc']} | "
                                f"📦 {kb:.1f} KB"
                            )
                        with col_dl:
                            fp, orig = get_file_path(row['id'])
                            if fp and fp.exists():
                                with open(fp, 'rb') as f:
                                    st.download_button("⬇️", data=f.read(), file_name=orig, key=f"dl_tl_{row['id']}")
                        with col_del:
                            with st.popover("🗑️"):
                                if st.button("Xóa", key=f"del_tl_db_{row['id']}", type="primary"):
                                    delete_tai_lieu(row['id'])
                                    st.rerun()

        st.markdown("---")

        # Preview staging
        staged_files = st.session_state.get("nl_staging_tai_lieu", [])
        if staged_files:
            st.markdown(f"**📋 Danh sách file chờ upload ({len(staged_files)} file):**")
            for i, item in enumerate(staged_files):
                col_info, col_del = st.columns([5, 1])
                with col_info:
                    st.markdown(f"↳ **{item['loai']}**: {item['file'].name} ({item['file'].size / 1024:.1f} KB)")
                with col_del:
                    if st.button("🗑️", key=f"del_tl_staging_{i}"):
                        st.session_state.nl_staging_tai_lieu.pop(i)
                        st.rerun()

        # Form upload mới
        st.markdown("##### ➕ Thêm tài liệu")
        st.caption(f"📌 Định dạng hỗ trợ: {', '.join(ALLOWED_EXTENSIONS)} | Giới hạn: {MAX_FILE_SIZE_MB}MB/file")

        uploaded_file = st.file_uploader(
            "Chọn file", type=ALLOWED_EXTENSIONS, key="upload_tai_lieu_input"
        )

        col1, col2 = st.columns(2)
        with col1:
            loai_tai_lieu = st.selectbox("Loại tài liệu", LOAI_TAI_LIEU_OPTIONS, key="tl_loai")
        with col2:
            mo_ta_tl = st.text_input("Mô tả (tùy chọn)", key="tl_mo_ta")

        if st.button("➕ Thêm vào danh sách", key="btn_add_tl", use_container_width=True):
            if uploaded_file:
                # Validate size
                if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
                    st.error(f"❌ File quá lớn! Giới hạn {MAX_FILE_SIZE_MB}MB")
                else:
                    st.session_state.nl_staging_tai_lieu.append({
                        "file": uploaded_file,
                        "loai": loai_tai_lieu,
                        "mo_ta": mo_ta_tl,
                    })
                    st.toast(f"✅ Đã thêm file: {uploaded_file.name}", icon="📋")
                    st.rerun()
            else:
                st.warning("⚠️ Vui lòng chọn file!")

    # ==================================================================
    # SECTION LƯU TOÀN BỘ HỒ SƠ (NGOÀI TABS)
    # ==================================================================
    st.markdown("---")
    st.markdown("### 💾 Lưu toàn bộ hồ sơ")

    # Tổng kết các mục chờ lưu
    cccd_val = st.session_state.get("nl_cccd", "")
    ho_ten_val = st.session_state.get("nl_ho_ten", "")
    them_bo_sung = st.session_state.get("nl_them_bo_sung", False)

    counts = {
        "Thân nhân": len(st.session_state.get("nl_staging_nhan_than", [])),
        "Quá trình": len(st.session_state.get("nl_staging_qt", [])),
        "Liên hệ": len(st.session_state.get("nl_staging_lien_he", [])),
        "Tài khoản NH": len(st.session_state.get("nl_staging_tai_chinh", [])),
        "Phương tiện": len(st.session_state.get("nl_staging_phuong_tien", [])),
        "Hồ sơ đặc thù": len(st.session_state.get("nl_staging_dac_thu", [])),
        "Tài liệu": len(st.session_state.get("nl_staging_tai_lieu", [])),
    }
    total_items = sum(counts.values())

    # Hiển thị tóm tắt
    summary_parts = [f"**{v}** {k}" for k, v in counts.items() if v > 0]
    if summary_parts or cccd_val:
        with st.container(border=True):
            st.markdown("**📊 Sẽ lưu:**")
            if not them_bo_sung:
                st.markdown(f"- 👤 Thông tin cá nhân: CCCD **{cccd_val or '—'}** | {ho_ten_val or '—'}")
            else:
                st.markdown(f"- 🔄 Bổ sung cho CCCD **{cccd_val}** (không ghi đè thông tin cá nhân)")
            if summary_parts:
                st.markdown("- " + " | ".join(summary_parts))
            else:
                st.caption("_(Chưa có dữ liệu vệ tinh nào được thêm)_")

    col_save, col_reset, _ = st.columns([2, 1, 3])

    with col_save:
        if st.button("✅ Lưu toàn bộ hồ sơ", type="primary", use_container_width=True, key="btn_save_all"):
            _do_save_all(
                cccd_val, ho_ten_val, them_bo_sung,
                st.session_state.get("main_ngay_sinh"),
                gioi_tinh if "gioi_tinh" in dir() else None,
                dia_chi_tinh if "dia_chi_tinh" in dir() else "Phú Thọ",
                dia_chi_xa if "dia_chi_xa" in dir() else "",
                dia_chi_chi_tiet if "dia_chi_chi_tiet" in dir() else "",
                phan_loai if "phan_loai" in dir() else "",
                chi_tiet_nghe if "chi_tiet_nghe" in dir() else "",
                ghi_chu if "ghi_chu" in dir() else "",
                avatar_file if "avatar_file" in dir() else None,
            )

    with col_reset:
        if st.button("🔄 Làm mới", use_container_width=True, key="btn_reset_all"):
            _reset_form()
            st.rerun()


# ===================================================================
# Batch save logic (tách ra để dễ test)
# ===================================================================
def _do_save_all(cccd, ho_ten, them_bo_sung,
                 ngay_sinh, gioi_tinh, dia_chi_tinh, dia_chi_xa, dia_chi_chi_tiet,
                 phan_loai, chi_tiet_nghe, ghi_chu, avatar_file):
    """Thực hiện lưu toàn bộ hồ sơ. Gọi từ nút Lưu toàn bộ."""

    # --- Validate bắt buộc ---
    if not cccd or len(cccd) != 12:
        st.error("⚠️ Vui lòng nhập đúng 12 số CCCD (Tab 1)!")
        return
    if not cccd.isdigit():
        st.error("⚠️ CCCD chỉ gồm các chữ số!")
        return
    if not ho_ten:
        st.error("⚠️ Vui lòng nhập Họ tên (Tab 1)!")
        return

    errors = []
    saved_counts = {}

    # --- Lưu thông tin cá nhân chính ---
    is_edit_mode = st.session_state.get("nl_edit_mode", False)

    if is_edit_mode:
        # Chế độ sửa: UPDATE thông tin cá nhân đã có
        update_data = {
            'ho_ten': ho_ten,
            'ngay_sinh': ngay_sinh.strftime('%Y-%m-%d') if ngay_sinh else None,
            'gioi_tinh': gioi_tinh or '',
            'dia_chi_tinh': dia_chi_tinh or 'Phú Thọ',
            'dia_chi_xa': dia_chi_xa or '',
            'dia_chi_chi_tiet': dia_chi_chi_tiet or '',
            'phan_loai_nghe_nghiep': phan_loai or '',
            'chi_tiet_nghe_nghiep': chi_tiet_nghe or '',
            'ghi_chu_chung': ghi_chu or '',
        }
        ok, msg = update_doi_tuong(cccd, update_data)
        if not ok:
            st.error(f"❌ Lỗi cập nhật thông tin cá nhân: {msg}")
            return
        saved_counts["Cập nhật thông tin cá nhân"] = 1
    elif not them_bo_sung:
        if check_cccd_exists(cccd):
            st.error(f"⚠️ CCCD {cccd} đã tồn tại! Nếu muốn bổ sung, hãy refresh trang.")
            return

        data = {
            'cccd': cccd,
            'ho_ten': ho_ten,
            'ngay_sinh': ngay_sinh.strftime('%Y-%m-%d') if ngay_sinh else None,
            'gioi_tinh': gioi_tinh or '',
            'dia_chi_tinh': dia_chi_tinh or 'Phú Thọ',
            'dia_chi_xa': dia_chi_xa or '',
            'dia_chi_chi_tiet': dia_chi_chi_tiet or '',
            'phan_loai_nghe_nghiep': phan_loai or '',
            'chi_tiet_nghe_nghiep': chi_tiet_nghe or '',
            'ghi_chu_chung': ghi_chu or '',
            'avatar_file': avatar_file,
        }
        ok, msg = save_doi_tuong(data)
        if not ok:
            st.error(f"❌ Lỗi lưu thông tin cá nhân: {msg}")
            return

    # Sau đây, CCCD chắc chắn tồn tại trong DB
    # --- Lưu thân nhân ---
    nt_list = st.session_state.get("nl_staging_nhan_than", [])
    nt_ok = 0
    for item in nt_list:
        cccd_nt = item.get("cccd_nhan_than", "")
        if cccd_nt and len(cccd_nt) == 12 and cccd_nt.isdigit():
            if not check_cccd_exists(cccd_nt):
                save_doi_tuong({
                    'cccd': cccd_nt,
                    'ho_ten': item.get("ho_ten", ""),
                    'ngay_sinh': item.get("ngay_sinh"),
                    'gioi_tinh': item.get("gioi_tinh", ""),
                    'dia_chi_tinh': item.get("dia_chi_tinh", "Phú Thọ"),
                    'dia_chi_xa': item.get("dia_chi_xa", ""),
                    'dia_chi_chi_tiet': item.get("dia_chi_chi_tiet", ""),
                    'phan_loai_nghe_nghiep': item.get("nghe_nghiep", ""),
                    'ghi_chu_chung': f"Hồ sơ tạo tự động từ thân nhân của {cccd}"
                })

        if save_nhan_than(
            cccd=cccd,
            loai_quan_he=item["loai_quan_he"],
            ho_ten=item["ho_ten"],
            cccd_nhan_than=item.get("cccd_nhan_than", ""),
            ngay_sinh=item.get("ngay_sinh"),
            gioi_tinh=item.get("gioi_tinh", ""),
            dia_chi_tinh=item.get("dia_chi_tinh", ""),
            dia_chi_xa=item.get("dia_chi_xa", ""),
            dia_chi_chi_tiet=item.get("dia_chi_chi_tiet", ""),
            nghe_nghiep=item.get("nghe_nghiep", ""),
            noi_o=item.get("noi_o", ""),
            ghi_chu=item.get("ghi_chu", ""),
        ):
            nt_ok += 1
        else:
            errors.append(f"Lỗi lưu thân nhân: {item['ho_ten']}")
    if nt_ok:
        saved_counts["thân nhân"] = nt_ok

    # --- Lưu quá trình hoạt động ---
    qt_list = st.session_state.get("nl_staging_qt", [])
    qt_ok = 0
    for item in qt_list:
        try:
            save_qua_trinh_hoat_dong(cccd, item["thoi_gian"], item["noi_dung"], item.get("ghi_chu", ""))
            qt_ok += 1
        except Exception as e:
            errors.append(f"Lỗi lưu quá trình: {e}")
    if qt_ok:
        saved_counts["quá trình hoạt động"] = qt_ok

    # --- Lưu liên hệ ---
    lh_list = st.session_state.get("nl_staging_lien_he", [])
    lh_ok = 0
    for item in lh_list:
        if save_lien_he(cccd, item["loai"], item["gia_tri"], item.get("ghi_chu", "")):
            lh_ok += 1
        else:
            errors.append(f"Lỗi lưu liên hệ: {item['gia_tri']}")
    if lh_ok:
        saved_counts["liên hệ"] = lh_ok

    # --- Lưu tài chính ---
    tc_list = st.session_state.get("nl_staging_tai_chinh", [])
    tc_ok = 0
    for item in tc_list:
        if save_tai_chinh(cccd, item["ngan_hang"], item["so_tai_khoan"], item.get("chu_tai_khoan", "")):
            tc_ok += 1
        else:
            errors.append(f"Lỗi lưu tài khoản: {item['so_tai_khoan']}")
    if tc_ok:
        saved_counts["tài khoản NH"] = tc_ok

    # --- Lưu phương tiện ---
    pt_list = st.session_state.get("nl_staging_phuong_tien", [])
    pt_ok = 0
    for item in pt_list:
        if save_phuong_tien(cccd, item["loai_xe"], item["bien_so"], item.get("ten_xe", "")):
            pt_ok += 1
        else:
            errors.append(f"Lỗi lưu phương tiện: {item['bien_so']}")
    if pt_ok:
        saved_counts["phương tiện"] = pt_ok

    # --- Lưu hồ sơ đặc thù ---
    dt_list = st.session_state.get("nl_staging_dac_thu", [])
    dt_ok = 0
    for item in dt_list:
        if save_ho_so_dac_thu(cccd, item["loai_hinh"], item["noi_dung"], item.get("ghi_chu", "")):
            dt_ok += 1
        else:
            errors.append(f"Lỗi lưu hồ sơ đặc thù: {item['loai_hinh']}")
    if dt_ok:
        saved_counts["hồ sơ đặc thù"] = dt_ok

    # --- Lưu tài liệu ---
    tl_list = st.session_state.get("nl_staging_tai_lieu", [])
    tl_ok = 0
    for item in tl_list:
        ok, msg = save_tai_lieu(cccd, item["file"], item["loai"], item.get("mo_ta", ""))
        if ok:
            tl_ok += 1
        else:
            errors.append(f"Lỗi upload file {item['file'].name}: {msg}")
    if tl_ok:
        saved_counts["tài liệu"] = tl_ok

    # --- Kết quả ---
    if errors:
        for e in errors:
            st.warning(f"⚠️ {e}")

    if saved_counts or not them_bo_sung:
        summary_str = " | ".join([f"**{v}** {k}" for k, v in saved_counts.items()])
        action = "bổ sung" if them_bo_sung else "tạo mới"
        st.success(
            f"✅ Đã {action} hồ sơ **{ho_ten}** (CCCD: {cccd})"
            + (f"\n\n📊 {summary_str}" if summary_str else "")
        )
        st.session_state.current_cccd = cccd

        # Xóa staging sau khi lưu thành công
        for k in ["nl_staging_nhan_than", "nl_staging_qt", "nl_staging_lien_he",
                  "nl_staging_tai_chinh", "nl_staging_phuong_tien",
                  "nl_staging_dac_thu", "nl_staging_tai_lieu"]:
            st.session_state[k] = []
        st.session_state.nl_edit_mode = False

        if not errors:
            st.balloons()
