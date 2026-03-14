# -*- coding: utf-8 -*-
"""
SECURITY PROFILE 360
Hệ thống Quản trị An ninh PA01
Phiên bản: 1.0 (với Authentication)
"""

from views.audit_log import page_audit_log, add_audit_log, get_client_ip
from views.nguon_du_lieu import page_nguon_du_lieu
import streamlit as st
import logging
from pathlib import Path
import time

from database import get_connection

# Import database module
from database import create_tables

# Import authentication
from app.services.auth_service import init_super_admin, is_super_admin

# Import login views
from views.login import (
    require_login,
    show_user_menu,
    show_self_change_password,
    get_current_user
)

# Import views
from views import (
    page_dashboard,
    page_nhap_lieu,
    page_tra_cuu,
    page_profile_view,
    page_ra_soat,
    page_nhap_excel
)
from views.quan_ly_user import page_quan_ly_user

# ============================================
# LOGGING CONFIGURATION
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# CẤU HÌNH TRANG
# ============================================
st.set_page_config(
    page_title="Security Profile 360",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================
# LOAD CSS
# ============================================


# @st.cache_data # Tắt cache để CSS mới được cập nhật ngay lập tức
def load_css():
    """Load custom CSS file (cached for performance)"""
    css_file = Path(__file__).parent / "style.css"
    if css_file.exists():
        with open(css_file, "r", encoding="utf-8") as f:
            return f.read()
    return ""


css_content = load_css()
if css_content:
    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)

# ============================================
# KHỞI TẠO DATABASE & SUPER ADMIN
# ============================================

@st.cache_resource
def init_database():
    """Khởi tạo database và Super Admin nếu chưa tồn tại"""
    create_tables()
    init_super_admin()
    return True


init_database()

# ============================================
# SESSION STATE INITIALIZATION
# ============================================
if 'form_submitted' not in st.session_state:
    st.session_state.form_submitted = False
if 'current_cccd' not in st.session_state:
    st.session_state.current_cccd = None
if 'view_profile_cccd' not in st.session_state:
    st.session_state.view_profile_cccd = None
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False
if 'confirm_delete' not in st.session_state:
    st.session_state.confirm_delete = False
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'show_change_password' not in st.session_state:
    st.session_state.show_change_password = False

# If form submitted, update last_active to prevent timeout during long entry
if st.session_state.form_submitted:
    st.session_state.last_active = time.time()

# ============================================
# SESSION TIMEOUT CHECK (30 minutes)
# ============================================
SESSION_TIMEOUT = 1800  # 30 minutes

if 'last_active' not in st.session_state:
    st.session_state.last_active = time.time()

if st.session_state.logged_in:
    if time.time() - st.session_state.last_active > SESSION_TIMEOUT:
        st.session_state.logged_in = False
        st.session_state.user = None
        st.error("⚠️ Phiên làm việc đã hết hạn do không hoạt động. Vui lòng đăng nhập lại.")
        st.stop()
    else:
        # Update activity time
        st.session_state.last_active = time.time()

# ============================================
# AUTHENTICATION CHECK
# ============================================
if not require_login():
    # Nếu chưa đăng nhập hoặc cần đổi mật khẩu, dừng ở đây
    st.stop()

# ============================================
# SIDEBAR & NAVIGATION (Sau khi đăng nhập)
# ============================================

# Import thêm các trang admin

with st.sidebar:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        logo_path = Path(__file__).parent / "logo.png"
        if logo_path.exists():
            st.image(str(logo_path), use_container_width=True)
        else:
            st.error(f"Logo not found at {logo_path}")
    st.markdown("<h3 style='text-align: center; margin-bottom: 0px;'>Security Profile PA01</h3>",
                unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #e0e0e0; font-weight: 600; font-size: 8px;'>HỆ THỐNG QUẢN LÝ HỒ SƠ CSXH</p>", unsafe_allow_html=True)

    st.markdown("---")

    # Menu items based on role
    user = get_current_user()

    menu_items = ["Dashboard", "Nhập liệu", "Nhập Excel", "Tra cứu", "Rà soát"]

    # Thêm menu Admin cho Super Admin
    if is_super_admin(user):
        menu_items.append("---")  # Separator
        menu_items.append("👥 Quản lý tài khoản")
        menu_items.append("📦 Nguồn dữ liệu")
        menu_items.append("📜 Lịch sử thay đổi")

    # Filter out separator
    display_menu = [m for m in menu_items if m != "---"]

    menu = st.radio(
        "Menu chính",
        display_menu,
        index=0,
        key="main_menu"
    )

    # User menu (đổi mật khẩu, đăng xuất)
    show_user_menu()

    st.markdown("---")
    st.markdown("<div style='text-align: center; color: #888; font-size: 0.8em;'>Thiết kế bởi Vi Phương</div>",
                unsafe_allow_html=True)

# ============================================
# ROUTING LOGIC
# ============================================

# Nếu đang đổi mật khẩu (tự nguyện)
if st.session_state.get('show_change_password'):
    show_self_change_password()

# Xử lý điều hướng đặc biệt (Xem chi tiết hồ sơ)
elif st.session_state.view_profile_cccd:
    # AUDIT LOGGING: Chỉ ghi log VIEW lần đầu trong ngày cho mỗi (user, hồ sơ)
    try:
        user = get_current_user()
        username = user.get('username') if user else 'Unknown'
        cccd = st.session_state.view_profile_cccd

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) 
            FROM audit_log 
            WHERE bang = ? 
              AND hanh_dong = 'VIEW' 
              AND khoa_chinh = ? 
              AND nguoi_thuc_hien = ? 
              AND DATE(created_at) = DATE('now','localtime')
            """,
            ('doi_tuong', cccd, username),
        )
        already_logged = cursor.fetchone()[0] > 0
        conn.close()

        if not already_logged:
            add_audit_log(
                bang='doi_tuong',
                hanh_dong='VIEW',
                khoa_chinh=cccd,
                du_lieu_cu='',
                du_lieu_moi='Xem chi tiết hồ sơ',
                nguoi_thuc_hien=username,
                ip_address=get_client_ip(),
            )
    except Exception:
        # Không chặn luồng xem hồ sơ nếu log lỗi
        pass
        
    page_profile_view(st.session_state.view_profile_cccd)

else:
    # Điều hướng theo menu sidebar
    if menu == "Dashboard":
        page_dashboard()
    elif menu == "Nhập liệu":
        page_nhap_lieu()
    elif menu == "Nhập Excel":
        page_nhap_excel()
    elif menu == "Tra cứu":
        page_tra_cuu()
    elif menu == "Rà soát":
        page_ra_soat()
    elif menu == "👥 Quản lý tài khoản":
        page_quan_ly_user()
    elif menu == "📦 Nguồn dữ liệu":
        page_nguon_du_lieu()
    elif menu == "📜 Lịch sử thay đổi":
        page_audit_log()
    else:
        page_dashboard()
