# -*- coding: utf-8 -*-
import streamlit as st
import logging
import re
import uuid
import shutil
import json
from datetime import datetime, date
from pathlib import Path
from database import get_connection, save_qua_trinh_hoat_dong, get_qua_trinh_hoat_dong, delete_qua_trinh_hoat_dong
from constants import (
    GIOI_TINH_OPTIONS, TINH_OPTIONS, DANH_SACH_XA_PHU_THO,
    PHAN_LOAI_NGHE_NGHIEP_OPTIONS, LOAI_LIEN_HE_OPTIONS,
    DANH_SACH_NGAN_HANG, LOAI_XE_OPTIONS, LOAI_HINH_DAC_THU,
    DANH_SACH_QUOC_GIA, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB,
    LOAI_TAI_LIEU_OPTIONS, Messages
)

from views.ho_so_chi_tiet import (
    get_nhan_than_by_cccd, get_lien_he_by_cccd,
    get_tai_chinh_by_cccd, get_phuong_tien_by_cccd,
    get_ho_so_dac_thu_by_cccd, get_tai_lieu_by_cccd,
    get_file_path, delete_nhan_than, delete_lien_he,
    delete_tai_chinh, delete_phuong_tien, delete_ho_so_dac_thu,
    delete_tai_lieu
)

from services import (
    check_cccd_exists, sanitize_filename, get_upload_folder,
    save_doi_tuong, save_lien_he, save_tai_chinh,
    save_phuong_tien, save_nhan_than, save_tai_lieu,
    save_ho_so_dac_thu
)

logger = logging.getLogger(__name__)

# ============================================
# HELPER FUNCTIONS
# ============================================

def validate_cccd_for_action(cccd: str, *required_fields) -> tuple[bool, str | None]:
    if not cccd:
        return False, Messages.MISSING_REQUIRED
    if not cccd.strip():
        return False, Messages.MISSING_REQUIRED
    for field in required_fields:
        if not field:
            return False, Messages.MISSING_REQUIRED
    if not check_cccd_exists(cccd):
        return False, Messages.CCCD_NOT_FOUND
    return True, None


# ============================================
# NHAP LIEU PAGE
# ============================================
def page_nhap_lieu():
    """Trang Nhập liệu - Form thêm mới đối tượng"""
    st.markdown("# 📝 Nhập liệu")
    st.markdown("### Thêm mới hồ sơ đối tượng")
    
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
    
    with tab1:
        st.markdown("#### 📋 Thông tin cơ bản")
        
        col1, col2 = st.columns(2)
        
        with col1:
            cccd = st.text_input(
                "Số CCCD *", 
                placeholder="Nhập 12 số CCCD",
                max_chars=12,
                help="Số căn cước công dân 12 số"
            )
            
            ho_ten = st.text_input(
                "Họ và tên *", 
                placeholder="Nguyễn Văn A",
                help="Họ tên đầy đủ theo giấy tờ"
            )

            # Avatar Upload (Mới)
            st.markdown("##### 📸 Ảnh đại diện")
            avatar_file = st.file_uploader("Tải lên ảnh chân dung", type=['png', 'jpg', 'jpeg'], key="main_avatar_uploader")
            
            # Ngày sinh với format dd/mm/yyyy
            ngay_sinh = st.date_input(
                "Ngày sinh",
                value=None,
                min_value=date(1900, 1, 1),
                max_value=datetime.now().date(),
                format="DD/MM/YYYY",
                help="Chọn ngày sinh",
                key="main_ngay_sinh"
            )
            
            gioi_tinh = st.selectbox(
                "Giới tính", 
                GIOI_TINH_OPTIONS,
                help="Giới tính theo CCCD"
            )
        
        with col2:
            dia_chi_tinh = st.selectbox(
                "Tỉnh/TP", 
                TINH_OPTIONS,
                help="Tỉnh/Thành phố thường trú"
            )
            
            if dia_chi_tinh == "Phú Thọ":
                # Dropdown chọn xã/phường trực tiếp
                dia_chi_xa = st.selectbox(
                    "Xã/Phường",
                    ["-- Chọn xã/phường --"] + DANH_SACH_XA_PHU_THO,
                    key="xa_phuong_select",
                    help="Chọn xã/phường từ danh sách"
                )
                if dia_chi_xa == "-- Chọn xã/phường --":
                    dia_chi_xa = ""
            else:
                dia_chi_xa = st.text_input(
                    "Địa chỉ chi tiết",
                    placeholder="Số nhà, đường, xã/phường, quận/huyện, tỉnh/TP"
                )
            
            phan_loai = st.selectbox(
                "Phân loại nghề nghiệp", 
                PHAN_LOAI_NGHE_NGHIEP_OPTIONS,
                help="Phân loại công việc hiện tại"
            )
            
            chi_tiet_nghe = st.text_input(
                "Chi tiết nơi làm việc", 
                placeholder="Ví dụ: Công an tỉnh Phú Thọ",
                help="Tên cơ quan, tổ chức đang làm việc"
            )
        
        st.markdown("---")
        
        ghi_chu = st.text_area(
            "Ghi chú chung", 
            placeholder="Các thông tin ghi chú khác...",
            height=100,
            help="Ghi chú thêm về đối tượng"
        )
        
        st.markdown("---")
        
        # Nút lưu thông tin cá nhân
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
        
        with col_btn1:
            if st.button("💾 Lưu thông tin", type="primary", use_container_width=True):
                # Validate
                if not cccd or len(cccd) != 12:
                    st.error("⚠️ Vui lòng nhập đúng 12 số CCCD!")
                elif not ho_ten:
                    st.error("⚠️ Vui lòng nhập họ tên!")
                elif check_cccd_exists(cccd):
                    st.error(f"⚠️ CCCD {cccd} đã tồn tại trong hệ thống!")
                else:
                    # Lưu dữ liệu
                    data = {
                        'cccd': cccd,
                        'ho_ten': ho_ten,
                        'ngay_sinh': ngay_sinh.strftime('%Y-%m-%d') if ngay_sinh else None,
                        'gioi_tinh': gioi_tinh,
                        'dia_chi_tinh': dia_chi_tinh,
                        'dia_chi_xa': dia_chi_xa,
                        'phan_loai_nghe_nghiep': phan_loai,
                        'chi_tiet_nghe_nghiep': chi_tiet_nghe,
                        'ghi_chu_chung': ghi_chu,
                        'avatar_file': avatar_file # Pass file object to save function
                    }
                    
                    success, message = save_doi_tuong(data)
                    if success:
                        st.success(f"✅ Đã lưu hồ sơ: {ho_ten} ({cccd})")
                        st.session_state.current_cccd = cccd
                        st.balloons()
                    else:
                        st.error(f"❌ Lỗi: {message}")
        
        with col_btn2:
            if st.button("🔄 Làm mới", use_container_width=True):
                st.session_state.current_cccd = None
                st.rerun()
    
    # ===== TAB THÂN NHÂN (MỚI) =====
    with tab_nhan_than:
        st.markdown("#### 👨‍👩‍👧‍👦 Thông tin thân nhân")
        
        # Kiểm tra đã có CCCD chưa
        if st.session_state.current_cccd:
            st.success(f"📌 Đang thêm thân nhân cho CCCD: **{st.session_state.current_cccd}**")
            current_cccd_nt = st.session_state.current_cccd
        else:
            st.warning("⚠️ Vui lòng nhập và lưu thông tin cá nhân trước (Tab 1)")
            current_cccd_nt = st.text_input(
                "Hoặc nhập CCCD đã có",
                placeholder="Nhập CCCD để thêm thân nhân",
                max_chars=12,
                key="cccd_nhan_than_tab"
            )
        
        st.markdown("---")
        
        # Hiển thị danh sách thân nhân đã có (với nút xóa)
        if current_cccd_nt and check_cccd_exists(current_cccd_nt):
            df_nhan_than = get_nhan_than_by_cccd(current_cccd_nt)
            if not df_nhan_than.empty:
                st.markdown("##### 📋 Danh sách thân nhân đã lưu")
                
                for idx, row in df_nhan_than.iterrows():
                    col_info, col_del = st.columns([5, 1])
                    with col_info:
                        st.markdown(f"""
                        **{row['loai_quan_he']}**: {row['ho_ten']} | 
                        📅 {row['ngay_sinh'] if row['ngay_sinh'] else 'N/A'} | 
                        💼 {row['nghe_nghiep'] if row['nghe_nghiep'] else 'N/A'} | 
                        📍 {row['noi_o'] if row['noi_o'] else 'N/A'}
                        """)
                    with col_del:
                        if st.button("🗑️", key=f"nl_del_nt_{row['id']}", help=f"Xóa {row['ho_ten']}"):
                            delete_nhan_than(row['id'])
                            st.toast(f"✅ Đã xóa {row['loai_quan_he']}: {row['ho_ten']}")
                            st.rerun()
                st.markdown("---")
        
        # Form thêm thân nhân mới
        st.markdown("##### ➕ Thêm thân nhân mới")
        
        loai_quan_he = st.selectbox(
            "Loại quan hệ",
            ["Bố đẻ", "Mẹ đẻ", "Vợ/Chồng", "Anh/Chị em ruột", "Anh/Chị em họ", "Ông/Bà", "Con", "Bạn thân", "Đồng nghiệp", "Khác"],
            key="nt_loai_quan_he"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            nt_ho_ten = st.text_input("Họ và tên *", placeholder="Nguyễn Văn A", key="nt_ho_ten")
            nt_cccd = st.text_input("Số CCCD", placeholder="Nhập 12 số CCCD (nếu có)", key="nt_cccd")
            nt_ngay_sinh = st.date_input("Ngày sinh", value=None, key="nt_ngay_sinh", format="DD/MM/YYYY", min_value=date(1900, 1, 1), max_value=date(2100, 12, 31))
        with col2:
            nt_phan_loai_nghe = st.selectbox("Phân loại nghề nghiệp", PHAN_LOAI_NGHE_NGHIEP_OPTIONS, key="nt_phan_loai_nghe")
            nt_nghe_nghiep = st.text_input("Chi tiết nghề nghiệp", placeholder="Ví dụ: Giáo viên THPT, Nông dân...", key="nt_nghe_nghiep")
            nt_noi_o = st.text_input("Nơi ở hiện nay", placeholder="Địa chỉ hiện tại", key="nt_noi_o")
        
        nt_ghi_chu = st.text_input("Ghi chú", placeholder="Ghi chú thêm...", key="nt_ghi_chu")
        
        if st.button("💾 Lưu thân nhân", type="primary", use_container_width=True):
            if current_cccd_nt and nt_ho_ten:
                if check_cccd_exists(current_cccd_nt):
                    # Kết hợp phân loại và chi tiết nghề nghiệp
                    nghe_nghiep_full = f"{nt_phan_loai_nghe}: {nt_nghe_nghiep}" if nt_nghe_nghiep else nt_phan_loai_nghe
                    save_nhan_than(
                        cccd=current_cccd_nt,
                        loai_quan_he=loai_quan_he,
                        ho_ten=nt_ho_ten,
                        cccd_nhan_than=nt_cccd,
                        ngay_sinh=nt_ngay_sinh.strftime('%Y-%m-%d') if nt_ngay_sinh else None,
                        nghe_nghiep=nghe_nghiep_full,
                        noi_o=nt_noi_o,
                        ghi_chu=nt_ghi_chu
                    )
                    st.toast(f"✅ Đã thêm {loai_quan_he}: {nt_ho_ten}", icon="🎉")
                    st.rerun()
                else:
                    st.error("⚠️ CCCD không tồn tại trong hệ thống!")
            else:
                st.warning("⚠️ Vui lòng nhập họ tên thân nhân!")
    
    # ===== TAB QUÁ TRÌNH HOẠT ĐỘNG (Satellite Data Layer) =====
    with tab_qt:
        st.markdown("#### ⏳ Quá trình hoạt động (Lịch sử nhân thân)")
        
        # Kiểm tra đã có CCCD chưa
        if st.session_state.current_cccd:
            current_cccd_qt = st.session_state.current_cccd
        else:
            st.warning("⚠️ Vui lòng nhập và lưu thông tin cá nhân trước (Tab 1)")
            current_cccd_qt = st.text_input(
                "Hoặc nhập CCCD đã có",
                placeholder="Nhập CCCD để thêm quá trình",
                max_chars=12,
                key="cccd_qt_tab"
            )
        
        st.markdown("---")
        
        # Form nhập liệu
        with st.expander("➕ Thêm quá trình hoạt động", expanded=True):
            col_qt_time, col_qt_content = st.columns([1, 2])
            with col_qt_time:
                c1, c2 = st.columns(2)
                with c1:
                    qt_tu_nam = st.text_input("Từ năm", placeholder="2010", key="qt_tu_nam")
                with c2:
                    qt_den_nam = st.text_input("Đến năm", placeholder="2015", key="qt_den_nam")
            with col_qt_content:
                qt_noi_dung = st.text_area("Nội dung hoạt động", placeholder="Mô tả hoạt động...", height=100, key="qt_noi_dung")
            
            qt_ghi_chu = st.text_input("Ghi chú", placeholder="Ghi chú thêm...", key="qt_ghi_chu")
            
            if st.button("💾 Lưu quá trình", type="primary", use_container_width=True):
                if current_cccd_qt and qt_noi_dung:
                    if check_cccd_exists(current_cccd_qt):
                        # Combine time fields
                        if qt_tu_nam and qt_den_nam:
                            qt_thoi_gian = f"{qt_tu_nam} - {qt_den_nam}"
                        elif qt_tu_nam:
                            qt_thoi_gian = f"Từ {qt_tu_nam}"
                        elif qt_den_nam:
                            qt_thoi_gian = f"Đến {qt_den_nam}"
                        else:
                            qt_thoi_gian = ""
                            
                        save_qua_trinh_hoat_dong(current_cccd_qt, qt_thoi_gian, qt_noi_dung, qt_ghi_chu)
                        st.toast("✅ Đã lưu quá trình hoạt động!", icon="🎉")
                        st.rerun()
                    else:
                        st.error("⚠️ CCCD không tồn tại trong hệ thống!")
                else:
                    st.warning("⚠️ Vui lòng nhập nội dung hoạt động!")

        # Hiển thị danh sách quá trình đã thêm (Preview)
        st.markdown("---")
        if current_cccd_qt and check_cccd_exists(current_cccd_qt):
            qt_list = get_qua_trinh_hoat_dong(current_cccd_qt)
            if qt_list:
                st.markdown("##### 📋 Danh sách đã thêm")
                for item in qt_list:
                    col_info, col_del = st.columns([5, 1])
                    with col_info:
                        st.markdown(f"**{item['thoi_gian']}**: {item['noi_dung']}")
                    with col_del:
                            if st.button("🗑️", key=f"del_qt_nl_{item['id']}"):
                                delete_qua_trinh_hoat_dong(item['id'])
                                st.rerun()

    with tab2:
        st.markdown("#### 📞 Thông tin liên hệ & Tài sản")
        
        # Kiểm tra đã có CCCD chưa
        if st.session_state.current_cccd:
            st.success(f"📌 Đang thêm thông tin cho CCCD: **{st.session_state.current_cccd}**")
            current_cccd = st.session_state.current_cccd
        else:
            st.warning("⚠️ Vui lòng nhập và lưu thông tin cá nhân trước (Tab 1)")
            current_cccd = st.text_input(
                "Hoặc nhập CCCD đã có",
                placeholder="Nhập CCCD để thêm thông tin",
                max_chars=12
            )
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 📱 Số điện thoại / Mạng xã hội")
            
            # Show existing contacts
            if current_cccd and check_cccd_exists(current_cccd):
                df_lien_he = get_lien_he_by_cccd(current_cccd)
                if not df_lien_he.empty:
                    with st.expander(f"📋 Danh sách liên hệ ({len(df_lien_he)})"):
                        for idx, row in df_lien_he.iterrows():
                             st.text(f"- {row['loai_lien_he']}: {row['gia_tri']}")

            loai_lien_he = st.selectbox("Loại liên hệ", LOAI_LIEN_HE_OPTIONS)
            gia_tri_lien_he = st.text_input(
                "Giá trị", 
                placeholder="0912345678 hoặc link FB/Zalo...",
                key="lien_he_value"
            )
            ghi_chu_lien_he = st.text_input("Ghi chú", key="lien_he_note", placeholder="Ghi chú thêm...")
            
            if st.button("💾 Lưu liên hệ", use_container_width=True, type="primary"):
                if current_cccd and gia_tri_lien_he:
                    if check_cccd_exists(current_cccd):
                        save_lien_he(current_cccd, loai_lien_he, gia_tri_lien_he, ghi_chu_lien_he)
                        st.toast(f"✅ Đã thêm {loai_lien_he}: {gia_tri_lien_he}", icon="🎉")
                        st.rerun()
                    else:
                        st.error("⚠️ CCCD không tồn tại trong hệ thống!")
                else:
                    st.warning("⚠️ Vui lòng nhập đầy đủ thông tin!")
        
        with col2:
            st.markdown("##### 🏦 Tài khoản ngân hàng")
            
            # Show existing financial records
            if current_cccd and check_cccd_exists(current_cccd):
                df_tai_chinh = get_tai_chinh_by_cccd(current_cccd)
                if not df_tai_chinh.empty:
                    with st.expander(f"📋 Danh sách tài khoản ({len(df_tai_chinh)})"):
                        for idx, row in df_tai_chinh.iterrows():
                             st.text(f"- {row['ngan_hang']}: {row['so_tai_khoan']}")

            ngan_hang = st.selectbox("Ngân hàng", DANH_SACH_NGAN_HANG, key="ngan_hang_tab2")
            so_tai_khoan = st.text_input("Số tài khoản", placeholder="1234567890")
            chu_tai_khoan = st.text_input("Chủ tài khoản", placeholder="NGUYEN VAN A")
            
            if st.button("💾 Lưu tài khoản", use_container_width=True, type="primary"):
                if current_cccd and so_tai_khoan:
                    if check_cccd_exists(current_cccd):
                        save_tai_chinh(current_cccd, ngan_hang, so_tai_khoan, chu_tai_khoan)
                        st.toast(f"✅ Đã thêm TK {ngan_hang}: {so_tai_khoan}", icon="🎉")
                        st.rerun()
                    else:
                        st.error("⚠️ CCCD không tồn tại trong hệ thống!")
                else:
                    st.warning("⚠️ Vui lòng nhập đầy đủ thông tin!")
        
        st.markdown("---")
        
        st.markdown("##### 🚗 Phương tiện giao thông")
        
        # Show existing vehicles
        if current_cccd and check_cccd_exists(current_cccd):
             df_phuong_tien = get_phuong_tien_by_cccd(current_cccd)
             if not df_phuong_tien.empty:
                 with st.expander(f"📋 Danh sách phương tiện ({len(df_phuong_tien)})"):
                        for idx, row in df_phuong_tien.iterrows():
                             st.text(f"- {row['loai_xe']}: {row['bien_kiem_soat']}")

        col1, col2, col3 = st.columns(3)
        with col1:
            loai_xe = st.selectbox("Loại xe", LOAI_XE_OPTIONS)
        with col2:
            bien_so = st.text_input("Biển kiểm soát", placeholder="19A-12345")
        with col3:
            ten_xe = st.text_input("Tên xe", placeholder="Honda Vision, Toyota Vios...")
        
        if st.button("💾 Lưu phương tiện", use_container_width=True, type="primary"):
            if current_cccd and bien_so:
                if check_cccd_exists(current_cccd):
                    save_phuong_tien(current_cccd, loai_xe, bien_so, ten_xe)
                    st.toast(f"✅ Đã thêm xe {loai_xe}: {bien_so}", icon="🎉")
                    st.rerun()
                else:
                    st.error("⚠️ CCCD không tồn tại trong hệ thống!")
            else:
                st.warning("⚠️ Vui lòng nhập đầy đủ thông tin!")
    
    with tab3:
        st.markdown("#### 🌐 Yếu tố nước ngoài & Nghiệp vụ")
        
        # Kiểm tra đã có CCCD chưa
        if st.session_state.current_cccd:
            st.success(f"📌 Đang thêm thông tin cho CCCD: **{st.session_state.current_cccd}**")
            current_cccd = st.session_state.current_cccd
        else:
            st.warning("⚠️ Vui lòng nhập và lưu thông tin cá nhân trước (Tab 1)")
            current_cccd = st.text_input(
                "Hoặc nhập CCCD đã có",
                placeholder="Nhập CCCD để thêm thông tin",
                max_chars=12,
                key="cccd_dac_thu"
            )
        
        st.markdown("---")
        
        loai_hinh = st.selectbox(
            "Loại hình hồ sơ đặc thù",
            options=list(LOAI_HINH_DAC_THU.keys()),
            format_func=lambda x: f"📌 {LOAI_HINH_DAC_THU[x]}"
        )
        
        st.markdown("---")
        
        noi_dung_dict = {}
        
        # Form động theo loại hình
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
            st.markdown("##### ⚠️ Thông tin vi phạm pháp luật ở nước ngoài")
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
        
        ghi_chu_dac_thu = st.text_area("Ghi chú thêm", placeholder="Ghi chú về hồ sơ đặc thù...", height=80)
        
        st.markdown("---")
        
        if st.button("💾 Lưu hồ sơ đặc thù", type="primary", use_container_width=True):
            if current_cccd:
                if check_cccd_exists(current_cccd):
                    # Kiểm tra có nội dung không
                    if any(noi_dung_dict.values()):
                        save_ho_so_dac_thu(current_cccd, loai_hinh, noi_dung_dict, ghi_chu_dac_thu)
                        st.toast(f"✅ Đã lưu hồ sơ đặc thù: {LOAI_HINH_DAC_THU[loai_hinh]}", icon="🎉")
                        st.rerun()
                    else:
                        st.warning("⚠️ Vui lòng nhập ít nhất một thông tin!")
                else:
                    st.error("⚠️ CCCD không tồn tại trong hệ thống! Vui lòng thêm thông tin cá nhân trước.")
            else:
                st.error("⚠️ Vui lòng nhập CCCD!")
        
        # Hiển thị danh sách hồ sơ đặc thù đã thêm
        st.markdown("---")
        if current_cccd and check_cccd_exists(current_cccd):
            df_csxh = get_ho_so_dac_thu_by_cccd(current_cccd)
            if not df_csxh.empty:
                st.markdown("##### 📋 Hồ sơ đặc thù đã thêm")
                st.caption("💡 Bạn có thể thêm nhiều loại hình CSXH cho cùng một người")
                
                for idx, row in df_csxh.iterrows():
                    loai_hinh_text = LOAI_HINH_DAC_THU.get(row['loai_hinh'], row['loai_hinh'])
                    col_info, col_del = st.columns([5, 1])
                    with col_info:
                        try:
                            noi_dung = json.loads(row['noi_dung_chi_tiet']) if row['noi_dung_chi_tiet'] else {}
                            info_preview = " | ".join([f"{v}" for v in list(noi_dung.values())[:2] if v])
                        except:
                            info_preview = ""
                        st.markdown(f"**📌 {loai_hinh_text}**: {info_preview}")
                    with col_del:
                        if st.button("🗑️", key=f"del_nl_csxh_{row['id']}", help=f"Xóa {loai_hinh_text}"):
                            if delete_ho_so_dac_thu(row['id']):
                                st.toast(f"✅ Đã xóa!", icon="🎉")
                                st.rerun()
            else:
                st.info("💡 Chọn loại hình và nhập thông tin để thêm hồ sơ đặc thù đầu tiên")
    
    # ===== TAB TÀI LIỆU ĐÍNH KÈM =====
    with tab_tai_lieu:
        st.markdown("#### 📎 Tài liệu đính kèm")
        
        # Kiểm tra đã có CCCD chưa
        if st.session_state.current_cccd:
            st.success(f"📌 Đang thêm tài liệu cho CCCD: **{st.session_state.current_cccd}**")
            current_cccd_tl = st.session_state.current_cccd
        else:
            st.warning("⚠️ Vui lòng nhập và lưu thông tin cá nhân trước (Tab 1)")
            current_cccd_tl = st.text_input(
                "Hoặc nhập CCCD đã có",
                placeholder="Nhập CCCD để thêm tài liệu",
                max_chars=12,
                key="cccd_tai_lieu_tab"
            )
        
        st.markdown("---")
        
        # Hiển thị danh sách tài liệu đã có
        if current_cccd_tl and check_cccd_exists(current_cccd_tl):
            df_tai_lieu = get_tai_lieu_by_cccd(current_cccd_tl)
            if not df_tai_lieu.empty:
                st.markdown("##### 📂 Danh sách tài liệu đã upload")
                
                for idx, row in df_tai_lieu.iterrows():
                    col_info, col_download, col_del = st.columns([4, 1, 1])
                    with col_info:
                        file_size_kb = row['dung_luong'] / 1024
                        st.markdown(f"""
                        **{row['loai_tai_lieu']}**: {row['ten_file_goc']} | 
                        📦 {file_size_kb:.1f} KB | 
                        📅 {row['created_at']}
                        """)
                        if row['mo_ta']:
                            st.caption(f"📝 {row['mo_ta']}")
                    with col_download:
                        file_path, original_name = get_file_path(row['id'])
                        if file_path and file_path.exists():
                            with open(file_path, 'rb') as f:
                                st.download_button(
                                    "⬇️",
                                    data=f.read(),
                                    file_name=original_name,
                                    key=f"dl_tl_{row['id']}",
                                    help="Tải xuống"
                                )
                    with col_del:
                        if st.button("🗑️", key=f"del_tl_{row['id']}", help=f"Xóa {row['ten_file_goc']}"):
                            delete_tai_lieu(row['id'])
                            st.toast(f"✅ Đã xóa: {row['ten_file_goc']}", icon="🎉")
                            st.rerun()
                st.markdown("---")
        
        # Form upload tài liệu mới
        st.markdown("##### ➕ Upload tài liệu mới")
        st.caption(f"📌 Định dạng hỗ trợ: {', '.join(ALLOWED_EXTENSIONS)} | Giới hạn: {MAX_FILE_SIZE_MB}MB/file")
        
        uploaded_file = st.file_uploader(
            "Chọn file",
            type=ALLOWED_EXTENSIONS,
            key="upload_tai_lieu"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            loai_tai_lieu = st.selectbox("Loại tài liệu", LOAI_TAI_LIEU_OPTIONS, key="tl_loai")
        with col2:
            mo_ta_tl = st.text_input("Mô tả (tùy chọn)", placeholder="Mô tả nội dung file...", key="tl_mo_ta")
        
        if st.button("💾 Upload tài liệu", type="primary", use_container_width=True):
            if current_cccd_tl and uploaded_file:
                if check_cccd_exists(current_cccd_tl):
                    success, message = save_tai_lieu(current_cccd_tl, uploaded_file, loai_tai_lieu, mo_ta_tl)
                    if success:
                        st.toast(f"✅ {message}: {uploaded_file.name}", icon="🎉")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("⚠️ CCCD không tồn tại trong hệ thống!")
            else:
                st.warning("⚠️ Vui lòng chọn file để upload!")
