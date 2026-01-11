# -*- coding: utf-8 -*-
"""
SECURITY PROFILE 360
Hệ thống Quản trị An ninh PA01
Phiên bản: 1.0
(Refactored)
"""

import streamlit as st
import logging
from pathlib import Path

# Import database module
from database import create_tables

# Import views
from views import (
    page_dashboard,
    page_nhap_lieu,
    page_tra_cuu,
    page_profile_view,
    page_ra_soat,
    page_nhap_excel
)

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
# KHỞI TẠO DATABASE
# ============================================
@st.cache_resource
def init_database():
    """Khởi tạo database nếu chưa tồn tại"""
    create_tables()
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

# ============================================
# SIDEBAR & NAVIGATION
# ============================================
with st.sidebar:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("logo.png", use_container_width=True)
    st.markdown("<h3 style='text-align: center; margin-bottom: 0px;'>Security Profile PA01</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #e0e0e0; font-weight: 600; font-size: 8px;'>HỆ THỐNG QUẢN LÝ HỒ SƠ CSXH</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    menu = st.radio(
        "Menu chính",
        ["Dashboard", "Nhập liệu", "Nhập Excel", "Tra cứu", "Rà soát"],
        index=0,
        key="main_menu"
    )
    
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: #888; font-size: 0.8em;'>Thiết kế bởi Vi Phương</div>", unsafe_allow_html=True)

# ============================================
# ROUTING LOGIC
# ============================================

# Xử lý điều hướng đặc biệt (Xem chi tiết hồ sơ)
if st.session_state.view_profile_cccd:
    # Nếu đang xem chi tiết, hiển thị trang profile
    # Bất kể menu đang chọn gì, trừ khi user click menu khác
    # Tuy nhiên Streamlit rerun script khi interact.
    # Logic: Nếu user click nút "Xem hồ sơ" ở trang Tra cứu, biến view_profile_cccd được set.
    # Script rerun. Tại đây ta check biến đó.
    # Để thoát chế độ xem chi tiết, View Profile cần có nút "Quay lại" set biến về None.
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
    else:
        page_dashboard()
