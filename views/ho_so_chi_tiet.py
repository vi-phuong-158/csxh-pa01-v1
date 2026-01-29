# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import json
import logging
import shutil
from pathlib import Path
from datetime import datetime, date
from database import (
    get_connection, get_qua_trinh_hoat_dong,
    save_qua_trinh_hoat_dong, delete_qua_trinh_hoat_dong
)
from constants import (
    GIOI_TINH_OPTIONS, TINH_OPTIONS, PHAN_LOAI_NGHE_NGHIEP_OPTIONS,
    LOAI_HINH_DAC_THU, LOAI_LIEN_HE_OPTIONS, DANH_SACH_NGAN_HANG,
    LOAI_XE_OPTIONS, DANH_SACH_QUOC_GIA, ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE_MB, LOAI_TAI_LIEU_OPTIONS, KET_QUA_XAC_MINH,
    HINH_THUC_DU_HOC
)

# Import từ services module để tránh circular import
from services import (
    save_nhan_than, save_lien_he, save_tai_chinh,
    save_phuong_tien, save_ho_so_dac_thu, save_tai_lieu,
    get_upload_folder
)

logger = logging.getLogger(__name__)

# ============================================
# SHARED GETTERS (Used by nhap_lieu and profile)
# ============================================


def get_doi_tuong_detail(cccd):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM doi_tuong WHERE cccd = ?", (cccd,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()


def get_nhan_than_by_cccd(cccd):
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM nhan_than WHERE cccd = ?", conn, params=(cccd,))
    conn.close()
    return df


def get_lien_he_by_cccd(cccd):
    conn = get_connection()
    query = "SELECT * FROM lien_he WHERE cccd = ? ORDER BY created_at DESC"
    df = pd.read_sql_query(query, conn, params=(cccd,))
    conn.close()
    return df


def get_tai_chinh_by_cccd(cccd):
    conn = get_connection()
    query = "SELECT * FROM tai_chinh WHERE cccd = ? ORDER BY created_at DESC"
    df = pd.read_sql_query(query, conn, params=(cccd,))
    conn.close()
    return df


def get_phuong_tien_by_cccd(cccd):
    conn = get_connection()
    query = "SELECT * FROM phuong_tien WHERE cccd = ? ORDER BY created_at DESC"
    df = pd.read_sql_query(query, conn, params=(cccd,))
    conn.close()
    return df


def get_ho_so_dac_thu_by_cccd(cccd):
    conn = get_connection()
    query = "SELECT * FROM ho_so_dac_thu WHERE cccd = ? ORDER BY created_at DESC"
    df = pd.read_sql_query(query, conn, params=(cccd,))
    conn.close()
    return df


def get_tai_lieu_by_cccd(cccd):
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM tai_lieu WHERE cccd = ? ORDER BY created_at DESC", conn, params=(cccd,))
    conn.close()
    return df


def get_file_path(tai_lieu_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT duong_dan, ten_file_goc FROM tai_lieu WHERE id = ?", (tai_lieu_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        # Resolve path relative to project root assuming app runs from root
        # If duong_dan doesn't start with 'uploads', we might need to adjust
        # In app.py: duong_dan = f"uploads/{cccd}/{unique_name}"
        # So it is relative to root.
        file_path = Path.cwd() / result[0]
        return file_path, result[1]
    return None, None

# ============================================
# SHARED DELETERS & UPDATERS
# ============================================


def delete_nhan_than(nhan_than_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM nhan_than WHERE id = ?", (nhan_than_id,))
    conn.commit()
    conn.close()
    return True


def delete_lien_he(lien_he_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM lien_he WHERE id = ?", (lien_he_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.exception(f"Lỗi xóa liên hệ: {e}")
        return False
    finally:
        conn.close()


def delete_tai_chinh(tai_chinh_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tai_chinh WHERE id = ?", (tai_chinh_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.exception(f"Lỗi xóa tài chính: {e}")
        return False
    finally:
        conn.close()


def delete_phuong_tien(phuong_tien_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM phuong_tien WHERE id = ?",
                       (phuong_tien_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.exception(f"Lỗi xóa phương tiện: {e}")
        return False
    finally:
        conn.close()


def delete_ho_so_dac_thu(ho_so_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ho_so_dac_thu WHERE id = ?", (ho_so_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.exception(f"Lỗi xóa hồ sơ đặc thù: {e}")
        return False
    finally:
        conn.close()


def delete_tai_lieu(tai_lieu_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT duong_dan FROM tai_lieu WHERE id = ?", (tai_lieu_id,))
    result = cursor.fetchone()

    if result:
        duong_dan = result[0]
        file_path = Path.cwd() / duong_dan
        if file_path.exists():
            file_path.unlink()

        cursor.execute("DELETE FROM tai_lieu WHERE id = ?", (tai_lieu_id,))
        conn.commit()

    conn.close()
    return True


def delete_doi_tuong(cccd):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM doi_tuong WHERE cccd = ?", (cccd,))
        conn.commit()

        upload_folder = Path.cwd() / "uploads" / cccd
        if upload_folder.exists():
            shutil.rmtree(upload_folder)

        return True, "Đã xóa thành công!"
    except Exception as e:
        logger.exception(f"Lỗi xóa đối tượng: {e}")
        return False, "Đã xảy ra lỗi hệ thống. Vui lòng thử lại."
    finally:
        conn.close()


def update_doi_tuong(cccd, data):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE doi_tuong 
            SET ho_ten = ?, ngay_sinh = ?, gioi_tinh = ?, dia_chi_tinh = ?,
                dia_chi_xa = ?, phan_loai_nghe_nghiep = ?, chi_tiet_nghe_nghiep = ?,
                ghi_chu_chung = ?, anh_chan_dung = ?, updated_at = CURRENT_TIMESTAMP
            WHERE cccd = ?
        """, (
            data['ho_ten'],
            data['ngay_sinh'],
            data['gioi_tinh'],
            data['dia_chi_tinh'],
            data['dia_chi_xa'],
            data['phan_loai_nghe_nghiep'],
            data['chi_tiet_nghe_nghiep'],
            data['ghi_chu_chung'],
            data.get('anh_chan_dung'),
            cccd
        ))
        conn.commit()
        return True, "Cập nhật thành công!"
    except Exception as e:
        logger.exception(f"Lỗi cập nhật đối tượng: {e}")
        return False, "Đã xảy ra lỗi hệ thống. Vui lòng thử lại."
    finally:
        conn.close()

# ============================================
# PROFILE VIEW PAGE
# ============================================


CSXH_FIELD_LABELS = {
    'ten_doi_tac': 'Tên đối tác',
    'quoc_tich': 'Quốc tịch',
    'so_ho_chieu': 'Số hộ chiếu',
    'tinh_trang': 'Tình trạng',
    'ten_to_chuc': 'Tên tổ chức',
    'chuc_vu': 'Chức vụ',
    'thoi_gian': 'Thời gian',
    'dia_diem': 'Địa điểm',
    'dien_di': 'Diện đi',
    'quoc_gia': 'Quốc gia',
    'thoi_gian_di': 'Thời gian đi',
    'thoi_gian_ve': 'Thời gian về',
    'nghe_sau_ve': 'Nghề sau khi về',
    'co_quan_bat': 'Cơ quan bắt giữ',
    'hinh_thuc_xu_ly': 'Hình thức xử lý',
    'noi_dung_vp': 'Nội dung vi phạm',
    'co_quan_xm': 'Cơ quan xác minh',
    'ket_qua': 'Kết quả',
    'noi_dung_xm': 'Nội dung xác minh',
}

# We need to import save functions from nhap_lieu IF they are needed here.
# But circular import again.
# The user asked to split logic.
# Profile view has "Edit mode" and "Add new item" forms.
# These forms use `save_...` functions.
# These `save_...` functions were in `nhap_lieu.py` in my previous step.
# Duplicating them violates DRY.
# Moving them to `ho_so_chi_tiet.py` or a `services` module is better.
# For this task, I will redefine them here or import them?
# If I import from `nhap_lieu` here, and `nhap_lieu` imports from here (getters), we have a cycle.
# Solution: Code duplication for `save_...` functions (simpler for now given constraints) OR move them to `ho_so_chi_tiet.py` as shared service functions and have `nhap_lieu` use them.
# I will move `save_...` functions to HERE (ho_so_chi_tiet.py) or `database.py` (not requested) or `services/` (implied but not explicit in file list).
# Re-reading task: "Tạo file views/nhap_lieu.py... Di chuyển hàm này và các hàm xử lý form (save_doi_tuong, save_lien_he...)"
# So `save_...` MUST be in `nhap_lieu.py`.
# Then `ho_so_chi_tiet.py` needs to Use them.
# To avoid circularity: I can import inside the function `page_profile_view`.


def page_profile_view(cccd):
    """Trang xem chi tiết hồ sơ đối tượng 360 độ"""
    # Save functions đã được import ở module level từ services

    # Lấy thông tin đối tượng
    doi_tuong = get_doi_tuong_detail(cccd)

    if not doi_tuong:
        st.error(f"❌ Không tìm thấy đối tượng với CCCD: {cccd}")
        if st.button("🔙 Quay lại Tra cứu"):
            st.session_state.view_profile_cccd = None
            st.rerun()
        return

    # Header với thông tin cơ bản
    st.markdown("# 👤 Hồ sơ Chi tiết")

    col_header1, col_header2, col_header3 = st.columns([1, 2, 1])

    with col_header1:
        # Avatar display logic
        avatar_path = doi_tuong.get('anh_chan_dung')
        has_avatar = False
        if avatar_path:
            # Check if file exists
            try:
                # Assuming path is relative to cwd
                full_avatar_path = Path.cwd() / avatar_path
                if full_avatar_path.exists():
                    st.image(str(full_avatar_path), width=150)
                    has_avatar = True
            except Exception:
                pass

        if not has_avatar:
            # Avatar placeholder
            st.markdown("""
            <div style="width: 120px; height: 120px; background: linear-gradient(135deg, #667eea, #764ba2); 
                        border-radius: 50%; display: flex; align-items: center; justify-content: center;
                        font-size: 48px; color: white; margin: 0 auto;">
                👤
            </div>
            """, unsafe_allow_html=True)

        # Quick avatar change expander
        with st.expander("📷 Thay ảnh đại diện", expanded=False):
            new_avatar_quick = st.file_uploader(
                "Chọn ảnh mới",
                type=['png', 'jpg', 'jpeg'],
                key="quick_avatar_uploader",
                label_visibility="collapsed"
            )
            if new_avatar_quick:
                if st.button("💾 Lưu ảnh", type="primary", use_container_width=True, key="save_quick_avatar"):
                    try:
                        import time
                        # Create user upload dir if not exists
                        upload_dir = get_upload_folder(cccd)
                        # Generate safe filename
                        file_ext = new_avatar_quick.name.split('.')[-1].lower()
                        safe_name = f"avatar_{int(time.time())}.{file_ext}"
                        save_path = upload_dir / safe_name

                        # Save file
                        with open(save_path, "wb") as f:
                            f.write(new_avatar_quick.getbuffer())

                        # Update database
                        new_avatar_path = f"uploads/{cccd}/{safe_name}"
                        conn = get_connection()
                        try:
                            cursor = conn.cursor()
                            cursor.execute(
                                "UPDATE doi_tuong SET anh_chan_dung = ?, updated_at = CURRENT_TIMESTAMP WHERE cccd = ?",
                                (new_avatar_path, cccd)
                            )
                            conn.commit()
                            st.success("✅ Đã cập nhật ảnh đại diện!")
                            st.rerun()
                        finally:
                            conn.close()
                    except Exception as e:
                        logger.error(f"Error saving quick avatar: {e}")
                        st.error("❌ Lỗi khi lưu ảnh!")

    with col_header2:
        st.markdown(f"## {doi_tuong.get('ho_ten', 'N/A')}")
        st.markdown(f"**CCCD:** {cccd}")

        # Tính tuổi
        if doi_tuong.get('ngay_sinh'):
            try:
                ngay_sinh = datetime.strptime(
                    str(doi_tuong['ngay_sinh']), '%Y-%m-%d')
                tuoi = (datetime.now() - ngay_sinh).days // 365
                st.markdown(
                    f"**Ngày sinh:** {ngay_sinh.strftime('%d/%m/%Y')} ({tuoi} tuổi)")
            except (ValueError, TypeError):
                st.markdown(
                    f"**Ngày sinh:** {doi_tuong.get('ngay_sinh', 'N/A')}")

        st.markdown(f"**Giới tính:** {doi_tuong.get('gioi_tinh', 'N/A')}")

    with col_header3:
        # Action buttons
        if st.button("🔙 Quay lại", use_container_width=True):
            st.session_state.view_profile_cccd = None
            st.session_state.edit_mode = False
            st.rerun()

        if st.button("✏️ Sửa hồ sơ", type="primary", use_container_width=True):
            st.session_state.edit_mode = True
            st.rerun()

        if st.button("🗑️ Xóa hồ sơ", type="secondary", use_container_width=True):
            st.session_state.confirm_delete = True

    # Xác nhận xóa
    if st.session_state.get('confirm_delete'):
        st.warning(
            f"⚠️ Bạn có chắc muốn xóa hồ sơ **{doi_tuong.get('ho_ten')}** không? Hành động này không thể hoàn tác!")
        col_del1, col_del2 = st.columns(2)
        with col_del1:
            if st.button("✅ Xác nhận xóa", type="primary"):
                success, msg = delete_doi_tuong(cccd)
                if success:
                    st.success(msg)
                    st.session_state.view_profile_cccd = None
                    st.session_state.confirm_delete = False
                    st.rerun()
                else:
                    st.error(msg)
        with col_del2:
            if st.button("❌ Hủy"):
                st.session_state.confirm_delete = False
                st.rerun()

    st.markdown("---")

    # Tabs chi tiết
    tab1, tab_nt, tab_qt, tab2, tab3, tab_tl = st.tabs([
        "📋 Thông tin cá nhân",
        "👨‍👩‍👧‍👦 Thân nhân",
        "⏳ Quá trình hoạt động",
        "📞 Liên hệ & Tài sản",
        "🌐 Yếu tố CSXH",
        "📎 Tài liệu"
    ])

    with tab1:
        st.markdown("#### 📋 Thông tin cá nhân")

        # Chế độ chỉnh sửa
        if st.session_state.get('edit_mode'):
            st.info("📝 **Chế độ chỉnh sửa** - Thay đổi thông tin và nhấn Lưu")

            with st.form("edit_form"):
                col1, col2 = st.columns(2)

                with col1:
                    # Avatar Upload
                    st.markdown("##### 📸 Ảnh đại diện")
                    new_avatar = st.file_uploader("Tải lên ảnh mới", type=[
                                                  'png', 'jpg', 'jpeg'], key="edit_avatar_uploader")

                    edit_ho_ten = st.text_input(
                        "Họ và tên *",
                        value=doi_tuong.get('ho_ten', ''),
                        key="edit_ho_ten"
                    )

                    # Ngày sinh

                    # Ngày sinh
                    current_ngay_sinh = doi_tuong.get('ngay_sinh')
                    ns_value = None
                    if current_ngay_sinh:
                        try:
                            ns_value = datetime.strptime(
                                str(current_ngay_sinh), '%Y-%m-%d').date()
                        except (ValueError, TypeError):
                            pass

                    edit_ngay_sinh_obj = st.date_input(
                        "Ngày sinh",
                        value=ns_value,
                        min_value=date(1900, 1, 1),
                        max_value=datetime.now().date(),
                        format="DD/MM/YYYY",
                        key="edit_ngay_sinh_picker"
                    )

                    edit_gioi_tinh = st.selectbox(
                        "Giới tính",
                        GIOI_TINH_OPTIONS,
                        index=GIOI_TINH_OPTIONS.index(doi_tuong.get('gioi_tinh', 'Nam')) if doi_tuong.get(
                            'gioi_tinh') in GIOI_TINH_OPTIONS else 0,
                        key="edit_gioi_tinh"
                    )

                with col2:
                    edit_dia_chi_tinh = st.selectbox(
                        "Tỉnh/TP",
                        TINH_OPTIONS,
                        index=TINH_OPTIONS.index(doi_tuong.get('dia_chi_tinh', 'Phú Thọ')) if doi_tuong.get(
                            'dia_chi_tinh') in TINH_OPTIONS else 0,
                        key="edit_dia_chi_tinh"
                    )

                    edit_dia_chi_xa = st.text_input(
                        "Xã/Phường",
                        value=doi_tuong.get('dia_chi_xa', ''),
                        key="edit_dia_chi_xa"
                    )

                    edit_phan_loai = st.selectbox(
                        "Phân loại nghề nghiệp",
                        PHAN_LOAI_NGHE_NGHIEP_OPTIONS,
                        index=PHAN_LOAI_NGHE_NGHIEP_OPTIONS.index(doi_tuong.get('phan_loai_nghe_nghiep', 'Lao động tự do')) if doi_tuong.get(
                            'phan_loai_nghe_nghiep') in PHAN_LOAI_NGHE_NGHIEP_OPTIONS else 0,
                        key="edit_phan_loai"
                    )

                    edit_chi_tiet_nghe = st.text_input(
                        "Chi tiết nơi làm việc",
                        value=doi_tuong.get('chi_tiet_nghe_nghiep', ''),
                        key="edit_chi_tiet_nghe"
                    )

                edit_ghi_chu = st.text_area(
                    "Ghi chú chung",
                    value=doi_tuong.get('ghi_chu_chung', ''),
                    height=100,
                    key="edit_ghi_chu"
                )

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    submitted = st.form_submit_button(
                        "💾 Lưu thay đổi", type="primary", use_container_width=True)
                with col_btn2:
                    cancel = st.form_submit_button(
                        "❌ Hủy", use_container_width=True)

                if submitted:
                    # Validate
                    if not edit_ho_ten:
                        st.error("⚠️ Vui lòng nhập họ tên!")
                    else:
                        # Parse ngày sinh
                        # Parse ngày sinh
                        edit_ngay_sinh = edit_ngay_sinh_obj.strftime(
                            '%Y-%m-%d') if edit_ngay_sinh_obj else None

                        # Handle Avatar Upload
                        current_avatar_path = doi_tuong.get('anh_chan_dung')
                        if new_avatar:
                            try:
                                # Create user upload dir if not exists
                                upload_dir = get_upload_folder(cccd)
                                # Generate safe filename
                                import time
                                file_ext = new_avatar.name.split('.')[-1]
                                # Clean filename
                                safe_name = f"avatar_{int(time.time())}.{file_ext}"
                                save_path = upload_dir / safe_name

                                # Save file
                                with open(save_path, "wb") as f:
                                    f.write(new_avatar.getbuffer())

                                # Update path (relative)
                                current_avatar_path = f"uploads/{cccd}/{safe_name}"
                            except Exception as e:
                                logger.error(f"Error saving avatar: {e}")
                                st.error("❌ Lỗi khi lưu ảnh đại diện!")

                        update_data = {
                            'ho_ten': edit_ho_ten,
                            'ngay_sinh': edit_ngay_sinh,
                            'gioi_tinh': edit_gioi_tinh,
                            'dia_chi_tinh': edit_dia_chi_tinh,
                            'dia_chi_xa': edit_dia_chi_xa,
                            'phan_loai_nghe_nghiep': edit_phan_loai,
                            'chi_tiet_nghe_nghiep': edit_chi_tiet_nghe,
                            'ghi_chu_chung': edit_ghi_chu,
                            'anh_chan_dung': current_avatar_path
                        }

                        success, msg = update_doi_tuong(cccd, update_data)
                        if success:
                            st.success(msg)
                            st.session_state.edit_mode = False
                            st.rerun()
                        else:
                            st.error(f"❌ Lỗi: {msg}")

                if cancel:
                    st.session_state.edit_mode = False
                    st.rerun()
        else:
            # Chế độ xem
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(
                    f"**Địa chỉ:** {doi_tuong.get('dia_chi_xa', '')} - {doi_tuong.get('dia_chi_tinh', '')}")
                st.markdown(
                    f"**Phân loại nghề nghiệp:** {doi_tuong.get('phan_loai_nghe_nghiep', 'N/A')}")

            with col2:
                st.markdown(
                    f"**Chi tiết nơi làm việc:** {doi_tuong.get('chi_tiet_nghe_nghiep', 'N/A')}")
                st.markdown(
                    f"**Ngày tạo:** {doi_tuong.get('created_at', 'N/A')}")

            if doi_tuong.get('ghi_chu_chung'):
                st.markdown("**Ghi chú:**")
                st.info(doi_tuong.get('ghi_chu_chung'))

    # ===== TAB THÂN NHÂN =====
    with tab_nt:
        st.markdown("#### 👨‍👩‍👧‍👦 Thông tin thân nhân")

        # Hiển thị danh sách thân nhân với nút xóa
        df_nhan_than = get_nhan_than_by_cccd(cccd)
        if not df_nhan_than.empty:
            st.markdown("##### 📋 Danh sách thân nhân")

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
                    with st.popover("🗑️", help=f"Xóa {row['ho_ten']}"):
                        st.markdown(f"Xóa **{row['ho_ten']}**?")
                        if st.button("Xác nhận", key=f"confirm_del_nt_{row['id']}", type="primary"):
                            delete_nhan_than(row['id'])
                            st.toast(f"✅ Đã xóa {row['loai_quan_he']}: {row['ho_ten']}", icon="✅")
                            st.rerun()
            st.markdown("---")
        else:
            st.info(
                "💡 Chưa có thông tin thân nhân. Nhấn **➕ Thêm thân nhân mới** để thêm.")

        # Form thêm thân nhân mới
        with st.expander("➕ Thêm thân nhân mới", expanded=False):
            with st.form("add_nhan_than_profile_form"):
                nt_loai_quan_he = st.selectbox(
                    "Loại quan hệ",
                    ["Bố đẻ", "Mẹ đẻ", "Vợ/Chồng", "Anh/Chị em ruột", "Anh/Chị em họ",
                        "Ông/Bà", "Con", "Bạn thân", "Đồng nghiệp", "Khác"],
                    key="pv_nt_loai"
                )

                col1, col2 = st.columns(2)
                with col1:
                    nt_ho_ten = st.text_input(
                        "Họ và tên *", key="pv_nt_ho_ten")
                    nt_cccd_nt = st.text_input(
                        "Số CCCD (nếu có)", key="pv_nt_cccd")
                    nt_ngay_sinh = st.date_input("Ngày sinh", value=None, key="pv_nt_ngay_sinh",
                                                 format="DD/MM/YYYY", min_value=date(1900, 1, 1), max_value=date(2100, 12, 31))
                with col2:
                    nt_phan_loai_nghe = st.selectbox(
                        "Phân loại nghề nghiệp", PHAN_LOAI_NGHE_NGHIEP_OPTIONS, key="pv_nt_phan_loai")
                    nt_nghe_nghiep = st.text_input(
                        "Chi tiết nghề nghiệp", placeholder="Ví dụ: Giáo viên THPT, Nông dân...", key="pv_nt_nghe")
                    nt_noi_o = st.text_input(
                        "Nơi ở hiện nay", key="pv_nt_noi_o")

                nt_ghi_chu = st.text_input("Ghi chú", key="pv_nt_ghi_chu")

                if st.form_submit_button("💾 Lưu thân nhân", type="primary"):
                    if nt_ho_ten:
                        # Kết hợp phân loại và chi tiết nghề nghiệp
                        nghe_nghiep_full = f"{nt_phan_loai_nghe}: {nt_nghe_nghiep}" if nt_nghe_nghiep else nt_phan_loai_nghe
                        save_nhan_than(
                            cccd=cccd,
                            loai_quan_he=nt_loai_quan_he,
                            ho_ten=nt_ho_ten,
                            cccd_nhan_than=nt_cccd_nt,
                            ngay_sinh=nt_ngay_sinh.strftime(
                                '%Y-%m-%d') if nt_ngay_sinh else None,
                            nghe_nghiep=nghe_nghiep_full,
                            noi_o=nt_noi_o,
                            ghi_chu=nt_ghi_chu
                        )
                        st.success(f"✅ Đã thêm {nt_loai_quan_he}: {nt_ho_ten}")
                        st.rerun()
                    else:
                        st.warning("⚠️ Vui lòng nhập họ tên!")

    # ===== TAB QUÁ TRÌNH HOẠT ĐỘNG =====
    with tab_qt:
        st.markdown("#### ⏳ Quá trình hoạt động & Lịch sử nhân thân")

        qt_list = get_qua_trinh_hoat_dong(cccd)

        if qt_list:
            # Hiển thị dạng Timeline đơn giản
            for item in qt_list:
                with st.container():
                    col_time, col_content, col_del = st.columns([1.5, 4, 0.5])
                    with col_time:
                        st.markdown(f"**{item['thoi_gian']}**")
                    with col_content:
                        st.markdown(item['noi_dung'])
                        if item['ghi_chu']:
                            st.caption(f"📝 {item['ghi_chu']}")
                    with col_del:
                        with st.popover("🗑️", help="Xóa mục này"):
                            st.markdown("Xóa quá trình này?")
                            if st.button("Xác nhận", key=f"confirm_del_qt_pv_{item['id']}", type="primary"):
                                if delete_qua_trinh_hoat_dong(item['id']):
                                    st.toast("✅ Đã xóa quá trình hoạt động", icon="✅")
                                    st.rerun()
                    st.divider()
        else:
            st.info("💡 Chưa có thông tin quá trình hoạt động")

        # Form thêm mới activity
        with st.expander("➕ Thêm hoạt động mới", expanded=False):
            with st.form("add_activity_profile_form"):
                col_qt_time, col_qt_content = st.columns([1, 3])
                with col_qt_time:
                    c1, c2 = st.columns(2)
                    with c1:
                        pv_qt_tu = st.text_input("Từ năm", key="pv_qt_tu")
                    with c2:
                        pv_qt_den = st.text_input("Đến năm", key="pv_qt_den")
                with col_qt_content:
                    qt_noi_dung = st.text_area(
                        "Nội dung", placeholder="Mô tả công việc, nơi ở...", key="pv_qt_nd")

                qt_ghi_chu = st.text_input("Ghi chú", key="pv_qt_gc")

                if st.form_submit_button("💾 Lưu hoạt động", type="primary"):
                    if qt_noi_dung:
                        # Combine time
                        if pv_qt_tu and pv_qt_den:
                            qt_thoi_gian = f"{pv_qt_tu} - {pv_qt_den}"
                        elif pv_qt_tu:
                            qt_thoi_gian = f"Từ {pv_qt_tu}"
                        elif pv_qt_den:
                            qt_thoi_gian = f"Đến {pv_qt_den}"
                        else:
                            qt_thoi_gian = ""

                        save_qua_trinh_hoat_dong(
                            cccd, qt_thoi_gian, qt_noi_dung, qt_ghi_chu)
                        st.success("✅ Đã thêm hoạt động!")
                        st.rerun()
                    else:
                        st.warning("⚠️ Vui lòng nhập nội dung!")

    with tab2:
        st.markdown("#### 📞 Liên hệ & Tài sản")

        # ========== LIÊN HỆ ==========
        st.markdown("##### 📱 Thông tin liên hệ")
        df_lien_he = get_lien_he_by_cccd(cccd)
        if not df_lien_he.empty:
            for idx, row in df_lien_he.iterrows():
                col_info, col_del = st.columns([5, 1])
                with col_info:
                    ghi_chu_text = f" | 📝 {row['ghi_chu']}" if row['ghi_chu'] else ""
                    st.markdown(
                        f"**{row['loai_lien_he']}**: {row['gia_tri']}{ghi_chu_text}")
                with col_del:
                    with st.popover("🗑️", help=f"Xóa {row['loai_lien_he']}"):
                        st.markdown(f"Xóa **{row['loai_lien_he']}**?")
                        if st.button("Xác nhận", key=f"confirm_del_lh_{row['id']}", type="primary"):
                            if delete_lien_he(row['id']):
                                st.toast("✅ Đã xóa liên hệ!", icon="✅")
                                st.rerun()
        else:
            st.info("💡 Chưa có thông tin liên hệ")

        # Form thêm liên hệ
        with st.expander("➕ Thêm liên hệ mới", expanded=False):
            with st.form("add_lien_he_form"):
                col1, col2 = st.columns(2)
                with col1:
                    lh_loai = st.selectbox(
                        "Loại liên hệ", LOAI_LIEN_HE_OPTIONS, key="add_lh_loai")
                    lh_gia_tri = st.text_input(
                        "Giá trị (SĐT/Email/Link...)", key="add_lh_gia_tri")
                with col2:
                    lh_ghi_chu = st.text_input("Ghi chú", key="add_lh_ghi_chu")

                if st.form_submit_button("💾 Lưu liên hệ", type="primary"):
                    if lh_gia_tri:
                        save_lien_he(cccd, lh_loai, lh_gia_tri, lh_ghi_chu)
                        st.success("✅ Đã thêm liên hệ!")
                        st.rerun()
                    else:
                        st.warning("⚠️ Vui lòng nhập giá trị!")

        st.markdown("---")

        # ========== TÀI KHOẢN NGÂN HÀNG ==========
        st.markdown("##### 🏦 Tài khoản ngân hàng")
        df_tai_chinh = get_tai_chinh_by_cccd(cccd)
        if not df_tai_chinh.empty:
            for idx, row in df_tai_chinh.iterrows():
                col_info, col_del = st.columns([5, 1])
                with col_info:
                    chu_tk = f" - {row['chu_tai_khoan']}" if row['chu_tai_khoan'] else ""
                    ghi_chu_text = f" | 📝 {row['ghi_chu']}" if row['ghi_chu'] else ""
                    st.markdown(
                        f"**{row['ngan_hang']}**: {row['so_tai_khoan']}{chu_tk}{ghi_chu_text}")
                with col_del:
                    with st.popover("🗑️", help=f"Xóa TK {row['ngan_hang']}"):
                        st.markdown(f"Xóa TK **{row['ngan_hang']}**?")
                        if st.button("Xác nhận", key=f"confirm_del_tc_{row['id']}", type="primary"):
                            if delete_tai_chinh(row['id']):
                                st.toast("✅ Đã xóa tài khoản!", icon="✅")
                                st.rerun()
        else:
            st.info("💡 Chưa có thông tin tài khoản ngân hàng")

        # Form thêm tài khoản
        with st.expander("➕ Thêm tài khoản ngân hàng", expanded=False):
            with st.form("add_tai_chinh_form"):
                col1, col2 = st.columns(2)
                with col1:
                    tc_ngan_hang = st.selectbox(
                        "Ngân hàng", DANH_SACH_NGAN_HANG, key="add_tc_ngan_hang")
                    tc_so_tk = st.text_input(
                        "Số tài khoản", key="add_tc_so_tk")
                with col2:
                    tc_chu_tk = st.text_input(
                        "Chủ tài khoản", key="add_tc_chu_tk")
                    tc_ghi_chu = st.text_input("Ghi chú", key="add_tc_ghi_chu")

                if st.form_submit_button("💾 Lưu tài khoản", type="primary"):
                    if tc_so_tk:
                        save_tai_chinh(cccd, tc_ngan_hang,
                                       tc_so_tk, tc_chu_tk, tc_ghi_chu)
                        st.success("✅ Đã thêm tài khoản!")
                        st.rerun()
                    else:
                        st.warning("⚠️ Vui lòng nhập số tài khoản!")

        st.markdown("---")

        # ========== PHƯƠNG TIỆN ==========
        st.markdown("##### 🚗 Phương tiện")
        df_phuong_tien = get_phuong_tien_by_cccd(cccd)
        if not df_phuong_tien.empty:
            for idx, row in df_phuong_tien.iterrows():
                col_info, col_del = st.columns([5, 1])
                with col_info:
                    ten_xe = f" - {row['ten_phuong_tien']}" if row['ten_phuong_tien'] else ""
                    ghi_chu_text = f" | 📝 {row['ghi_chu']}" if row['ghi_chu'] else ""
                    st.markdown(
                        f"**{row['loai_xe']}**: {row['bien_kiem_soat']}{ten_xe}{ghi_chu_text}")
                with col_del:
                    with st.popover("🗑️", help=f"Xóa {row['bien_kiem_soat']}"):
                        st.markdown(f"Xóa xe **{row['bien_kiem_soat']}**?")
                        if st.button("Xác nhận", key=f"confirm_del_pt_{row['id']}", type="primary"):
                            if delete_phuong_tien(row['id']):
                                st.toast("✅ Đã xóa phương tiện!", icon="✅")
                                st.rerun()
        else:
            st.info("💡 Chưa có thông tin phương tiện")

        # Form thêm phương tiện
        with st.expander("➕ Thêm phương tiện", expanded=False):
            with st.form("add_phuong_tien_form"):
                col1, col2 = st.columns(2)
                with col1:
                    pt_loai = st.selectbox(
                        "Loại xe", LOAI_XE_OPTIONS, key="add_pt_loai")
                    pt_bien_so = st.text_input(
                        "Biển kiểm soát", key="add_pt_bien_so")
                with col2:
                    pt_ten = st.text_input("Tên phương tiện", key="add_pt_ten")
                    pt_ghi_chu = st.text_input("Ghi chú", key="add_pt_ghi_chu")

                if st.form_submit_button("💾 Lưu phương tiện", type="primary"):
                    if pt_bien_so:
                        save_phuong_tien(
                            cccd, pt_loai, pt_bien_so, pt_ten, pt_ghi_chu)
                        st.success("✅ Đã thêm phương tiện!")
                        st.rerun()
                    else:
                        st.warning("⚠️ Vui lòng nhập biển kiểm soát!")

    with tab3:
        st.markdown("#### 🌐 Yếu tố CSXH (Đặc thù)")

        df_dac_thu = get_ho_so_dac_thu_by_cccd(cccd)

        if not df_dac_thu.empty:
            for idx, row in df_dac_thu.iterrows():
                loai_hinh = row['loai_hinh']
                loai_hinh_text = LOAI_HINH_DAC_THU.get(loai_hinh, loai_hinh)

                with st.expander(f"📌 {loai_hinh_text}", expanded=True):
                    # Parse JSON nội dung chi tiết
                    try:
                        noi_dung = json.loads(
                            row['noi_dung_chi_tiet']) if row['noi_dung_chi_tiet'] else {}
                    except (json.JSONDecodeError, TypeError):
                        noi_dung = {}

                    col1, col2 = st.columns(2)
                    items = list(noi_dung.items())
                    mid = len(items) // 2 + len(items) % 2

                    with col1:
                        for key, value in items[:mid]:
                            if value:
                                label = CSXH_FIELD_LABELS.get(
                                    key, key.replace('_', ' ').title())
                                st.markdown(f"**{label}:** {value}")

                    with col2:
                        for key, value in items[mid:]:
                            if value:
                                label = CSXH_FIELD_LABELS.get(
                                    key, key.replace('_', ' ').title())
                                st.markdown(f"**{label}:** {value}")

                    if row.get('ghi_chu'):
                        st.markdown(f"**Ghi chú:** {row['ghi_chu']}")

                    col_date, col_del = st.columns([4, 1])
                    with col_date:
                        st.caption(
                            f"📅 Ngày tạo: {row.get('created_at', 'N/A')}")
                    with col_del:
                        with st.popover("🗑️ Xóa", help=f"Xóa hồ sơ {loai_hinh_text}"):
                            st.markdown(f"Xóa hồ sơ **{loai_hinh_text}**?")
                            if st.button("Xác nhận", key=f"confirm_del_csxh_{row['id']}", type="primary"):
                                if delete_ho_so_dac_thu(row['id']):
                                    st.toast(f"✅ Đã xóa: {loai_hinh_text}", icon="✅")
                                    st.rerun()
                                else:
                                    st.error("❌ Lỗi khi xóa hồ sơ!")
        else:
            st.info("💡 Chưa có hồ sơ đặc thù nào")

        # Form thêm hồ sơ đặc thù mới - Dynamic fields based on type
        st.markdown("---")
        with st.expander("➕ Thêm hồ sơ đặc thù mới", expanded=False):
            # Chọn loại hình trước (ngoài form để có thể reactive)
            csxh_loai = st.selectbox(
                "Loại hình CSXH",
                list(LOAI_HINH_DAC_THU.keys()),
                format_func=lambda x: LOAI_HINH_DAC_THU.get(x, x),
                key="pv_csxh_loai_select"
            )

            with st.form("add_csxh_profile_form"):
                st.markdown("**Nội dung chi tiết:**")

                noi_dung = {}

                # Dynamic fields based on csxh_loai
                if csxh_loai == "Hon_Nhan_NN":
                    st.markdown("##### 💑 Thông tin đối tác nước ngoài")
                    col1, col2 = st.columns(2)
                    with col1:
                        noi_dung["ten_doi_tac"] = st.text_input(
                            "Họ tên đối tác", key="csxh_hn_ten")
                        noi_dung["quoc_tich"] = st.selectbox(
                            "Quốc tịch", DANH_SACH_QUOC_GIA, key="csxh_hn_qt")
                    with col2:
                        noi_dung["so_ho_chieu"] = st.text_input(
                            "Số hộ chiếu", key="csxh_hn_hc")
                        noi_dung["tinh_trang"] = st.selectbox(
                            "Tình trạng",
                            ["Kết hôn hợp pháp", "Sinh sống như vợ chồng",
                                "Đã ly hôn", "Đã qua đời"],
                            key="csxh_hn_tt"
                        )

                elif csxh_loai == "Lam_Viec_NN":
                    st.markdown("##### 🏢 Thông tin tổ chức nước ngoài")
                    noi_dung["ten_to_chuc"] = st.text_input(
                        "Tên tổ chức NGO/FDI", key="csxh_lv_tc")
                    col1, col2 = st.columns(2)
                    with col1:
                        noi_dung["chuc_vu"] = st.text_input(
                            "Chức vụ", key="csxh_lv_cv")
                    with col2:
                        noi_dung["thoi_gian"] = st.text_input(
                            "Thời gian làm việc", key="csxh_lv_tg")
                    noi_dung["dia_diem"] = st.text_input(
                        "Địa điểm làm việc", key="csxh_lv_dd")

                elif csxh_loai == "Hoc_Tap_Cong_Tac_NN":
                    st.markdown("##### 🎓 Thông tin du học/công tác nước ngoài")
                    col1, col2 = st.columns(2)
                    with col1:
                        noi_dung["dien_di"] = st.selectbox(
                            "Diện đi",
                            ["Du học tự túc", "Du học ngân sách",
                                "Công tác", "Xuất khẩu lao động", "Khác"],
                            key="csxh_ht_dien"
                        )
                        noi_dung["quoc_gia"] = st.selectbox(
                            "Quốc gia", DANH_SACH_QUOC_GIA, key="csxh_ht_qg")
                    with col2:
                        noi_dung["thoi_gian_di"] = st.text_input(
                            "Thời gian đi", key="csxh_ht_tgd")
                        noi_dung["thoi_gian_ve"] = st.text_input(
                            "Thời gian về", key="csxh_ht_tgv")
                    noi_dung["nghe_sau_ve"] = st.text_input(
                        "Nghề nghiệp sau khi về", key="csxh_ht_nghe")

                elif csxh_loai == "Vi_Pham_NN":
                    st.markdown(
                        "##### ⚠️ Thông tin vi phạm pháp luật ở nước ngoài")
                    col1, col2 = st.columns(2)
                    with col1:
                        noi_dung["quoc_gia"] = st.selectbox(
                            "Quốc gia", DANH_SACH_QUOC_GIA, key="csxh_vp_qg")
                        noi_dung["co_quan_bat"] = st.text_input(
                            "Cơ quan bắt giữ", key="csxh_vp_cq")
                    with col2:
                        vp_ngay = st.date_input(
                            "Ngày vi phạm", value=None, format="DD/MM/YYYY", key="csxh_vp_tg")
                        noi_dung["thoi_gian"] = vp_ngay.strftime(
                            "%d/%m/%Y") if vp_ngay else ""
                        noi_dung["hinh_thuc_xu_ly"] = st.text_input(
                            "Hình thức xử lý", key="csxh_vp_ht")
                    noi_dung["noi_dung_vp"] = st.text_area(
                        "Nội dung vi phạm", key="csxh_vp_nd", height=100)

                elif csxh_loai == "Xac_Minh":
                    st.markdown("##### 🔍 Thông tin xác minh")
                    col1, col2 = st.columns(2)
                    with col1:
                        noi_dung["co_quan_xm"] = st.text_input(
                            "Cơ quan xác minh", key="csxh_xm_cq")
                        xm_ngay = st.date_input(
                            "Ngày xác minh", value=None, format="DD/MM/YYYY", key="csxh_xm_tg")
                        noi_dung["thoi_gian"] = xm_ngay.strftime(
                            "%d/%m/%Y") if xm_ngay else ""
                    with col2:
                        noi_dung["ket_qua"] = st.selectbox(
                            "Kết quả",
                            ["Đủ điều kiện", "Không đủ điều kiện",
                                "Đang xác minh", "Khác"],
                            key="csxh_xm_kq"
                        )
                    noi_dung["noi_dung_xm"] = st.text_area(
                        "Nội dung xác minh", key="csxh_xm_nd", height=100)

                else:
                    # Default: generic fields
                    col1, col2 = st.columns(2)
                    with col1:
                        noi_dung["ten_doi_tac"] = st.text_input(
                            "Tên đối tác/Tổ chức", key="csxh_def_ten")
                        noi_dung["quoc_gia"] = st.selectbox(
                            "Quốc gia", DANH_SACH_QUOC_GIA, key="csxh_def_qg")
                    with col2:
                        noi_dung["thoi_gian"] = st.text_input(
                            "Thời gian", key="csxh_def_tg")
                        noi_dung["tinh_trang"] = st.text_input(
                            "Tình trạng", key="csxh_def_tt")

                csxh_ghi_chu = st.text_area(
                    "Ghi chú", key="pv_csxh_ghi_chu", height=80)

                if st.form_submit_button("💾 Lưu hồ sơ đặc thù", type="primary"):
                    # Kiểm tra có dữ liệu hợp lệ
                    has_data = any(v for v in noi_dung.values()
                                   if v) or csxh_ghi_chu
                    if has_data:
                        save_ho_so_dac_thu(
                            cccd, csxh_loai, noi_dung, csxh_ghi_chu)
                        st.success(
                            f"✅ Đã thêm hồ sơ: {LOAI_HINH_DAC_THU.get(csxh_loai, csxh_loai)}")
                        st.rerun()
                    else:
                        st.warning("⚠️ Vui lòng nhập thông tin!")

    # ===== TAB TÀI LIỆU =====
    with tab_tl:
        st.markdown("#### 📎 Tài liệu đính kèm")

        # Hiển thị danh sách tài liệu
        df_tai_lieu = get_tai_lieu_by_cccd(cccd)
        if not df_tai_lieu.empty:
            st.markdown("##### 📂 Danh sách tài liệu")

            for idx, row in df_tai_lieu.iterrows():
                col_info, col_download, col_del = st.columns([4, 1, 1])
                with col_info:
                    file_size_kb = row['dung_luong'] / 1024
                    # Preview ảnh nếu là file ảnh
                    if row['dinh_dang'] in ['jpg', 'jpeg', 'png', 'gif']:
                        file_path, _ = get_file_path(row['id'])
                        if file_path and file_path.exists():
                            st.image(str(file_path), width=200)
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
                                key=f"pv_dl_tl_{row['id']}",
                                help="Tải xuống"
                            )
                with col_del:
                    with st.popover("🗑️", help=f"Xóa {row['ten_file_goc']}"):
                        st.markdown(f"Xóa file **{row['ten_file_goc']}**?")
                        if st.button("Xác nhận", key=f"confirm_pv_del_tl_{row['id']}", type="primary"):
                            delete_tai_lieu(row['id'])
                            st.toast(f"✅ Đã xóa: {row['ten_file_goc']}", icon="✅")
                            st.rerun()
            st.markdown("---")
        else:
            st.info("💡 Chưa có tài liệu đính kèm")

        # Form upload tài liệu mới
        with st.expander("➕ Upload tài liệu mới", expanded=False):
            st.caption(
                f"📌 Định dạng hỗ trợ: {', '.join(ALLOWED_EXTENSIONS)} | Giới hạn: {MAX_FILE_SIZE_MB}MB/file")

            with st.form("pv_upload_tai_lieu_form"):
                uploaded_file = st.file_uploader(
                    "Chọn file",
                    type=ALLOWED_EXTENSIONS,
                    key="pv_upload_tai_lieu"
                )

                col1, col2 = st.columns(2)
                with col1:
                    loai_tai_lieu = st.selectbox(
                        "Loại tài liệu", LOAI_TAI_LIEU_OPTIONS, key="pv_tl_loai")
                with col2:
                    mo_ta_tl = st.text_input(
                        "Mô tả (tùy chọn)", key="pv_tl_mo_ta")

                if st.form_submit_button("💾 Upload", type="primary"):
                    if uploaded_file:
                        success, message = save_tai_lieu(
                            cccd, uploaded_file, loai_tai_lieu, mo_ta_tl)
                        if success:
                            st.success(f"✅ {message}: {uploaded_file.name}")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                    else:
                        st.warning("⚠️ Vui lòng chọn file để upload!")
