# -*- coding: utf-8 -*-
"""
SECURITY PROFILE 360
Hệ thống Quản trị An ninh PA01
Phiên bản: 1.0
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime, date
from pathlib import Path

# Import modules nội bộ
from database import get_connection, create_tables, get_db_path
from constants import (
    DANH_SACH_XA_PHU_THO,
    GIOI_TINH_OPTIONS,
    TINH_OPTIONS,
    PHAN_LOAI_NGHE_NGHIEP_OPTIONS,
    LOAI_LIEN_HE_OPTIONS,
    LOAI_XE_OPTIONS,
    LOAI_HINH_DAC_THU,
    DANH_SACH_NGAN_HANG,
    DANH_SACH_QUOC_GIA,
    LOAI_TAI_LIEU_OPTIONS,
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE_MB,
)
from bulk_import import create_excel_template, validate_excel_data, bulk_import_all, export_error_excel
import os
import shutil
import uuid

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
    """Load custom CSS file"""
    css_file = Path(__file__).parent / "style.css"
    if css_file.exists():
        with open(css_file, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

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
# HÀM TRUY VẤN DỮ LIỆU
# ============================================
def get_statistics():
    """Lấy thống kê tổng quan"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tổng số đối tượng
    cursor.execute("SELECT COUNT(*) FROM doi_tuong")
    total_doi_tuong = cursor.fetchone()[0]
    
    # Số theo giới tính
    cursor.execute("SELECT gioi_tinh, COUNT(*) FROM doi_tuong GROUP BY gioi_tinh")
    gioi_tinh_stats = dict(cursor.fetchall())
    
    # Số theo phân loại nghề nghiệp
    cursor.execute("SELECT phan_loai_nghe_nghiep, COUNT(*) FROM doi_tuong GROUP BY phan_loai_nghe_nghiep")
    nghe_nghiep_stats = dict(cursor.fetchall())
    
    # Số hồ sơ đặc thù theo loại hình
    cursor.execute("SELECT loai_hinh, COUNT(*) FROM ho_so_dac_thu GROUP BY loai_hinh")
    dac_thu_stats = dict(cursor.fetchall())
    
    conn.close()
    
    return {
        "total": total_doi_tuong,
        "gioi_tinh": gioi_tinh_stats,
        "nghe_nghiep": nghe_nghiep_stats,
        "dac_thu": dac_thu_stats,
    }

def get_recent_records(limit=10):
    """Lấy các bản ghi gần đây"""
    conn = get_connection()
    query = """
        SELECT cccd, ho_ten, ngay_sinh, gioi_tinh, dia_chi_xa, phan_loai_nghe_nghiep
        FROM doi_tuong
        ORDER BY created_at DESC
        LIMIT ?
    """
    df = pd.read_sql_query(query, conn, params=(limit,))
    conn.close()
    return df

def check_cccd_exists(cccd):
    """Kiểm tra CCCD đã tồn tại chưa"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM doi_tuong WHERE cccd = ?", (cccd,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

def save_doi_tuong(data):
    """Lưu thông tin đối tượng vào database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO doi_tuong (cccd, ho_ten, ngay_sinh, gioi_tinh, dia_chi_tinh, 
                                   dia_chi_xa, anh_chan_dung, phan_loai_nghe_nghiep, 
                                   chi_tiet_nghe_nghiep, ghi_chu_chung)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['cccd'],
            data['ho_ten'],
            data['ngay_sinh'],
            data['gioi_tinh'],
            data['dia_chi_tinh'],
            data['dia_chi_xa'],
            data.get('anh_chan_dung', ''),
            data['phan_loai_nghe_nghiep'],
            data['chi_tiet_nghe_nghiep'],
            data['ghi_chu_chung']
        ))
        conn.commit()
        conn.close()
        return True, "Lưu thành công!"
    except Exception as e:
        conn.close()
        return False, str(e)

def save_lien_he(cccd, loai, gia_tri, ghi_chu=""):
    """Lưu thông tin liên hệ"""
    if not gia_tri:
        return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO lien_he (cccd, loai_lien_he, gia_tri, ghi_chu)
        VALUES (?, ?, ?, ?)
    """, (cccd, loai, gia_tri, ghi_chu))
    conn.commit()
    conn.close()

def save_tai_chinh(cccd, ngan_hang, so_tai_khoan, chu_tai_khoan="", ghi_chu=""):
    """Lưu thông tin tài chính"""
    if not so_tai_khoan:
        return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tai_chinh (cccd, ngan_hang, so_tai_khoan, chu_tai_khoan, ghi_chu)
        VALUES (?, ?, ?, ?, ?)
    """, (cccd, ngan_hang, so_tai_khoan, chu_tai_khoan, ghi_chu))
    conn.commit()
    conn.close()

def save_phuong_tien(cccd, loai_xe, bien_so, ten_xe, ghi_chu=""):
    """Lưu thông tin phương tiện"""
    if not bien_so:
        return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO phuong_tien (cccd, loai_xe, bien_kiem_soat, ten_phuong_tien, ghi_chu)
        VALUES (?, ?, ?, ?, ?)
    """, (cccd, loai_xe, bien_so, ten_xe, ghi_chu))
    conn.commit()
    conn.close()

def save_nhan_than(cccd, loai_quan_he, ho_ten, cccd_nhan_than="", ngay_sinh=None, nghe_nghiep="", noi_o="", ghi_chu=""):
    """Lưu thông tin nhân thân"""
    if not ho_ten:
        return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO nhan_than (cccd, loai_quan_he, ho_ten, cccd_nhan_than, ngay_sinh, nghe_nghiep, noi_o, ghi_chu)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (cccd, loai_quan_he, ho_ten, cccd_nhan_than, ngay_sinh, nghe_nghiep, noi_o, ghi_chu))
    conn.commit()
    conn.close()

def get_nhan_than_by_cccd(cccd):
    """Lấy danh sách nhân thân theo CCCD"""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM nhan_than WHERE cccd = ?", conn, params=(cccd,))
    conn.close()
    return df

def delete_nhan_than(nhan_than_id):
    """Xóa thân nhân theo ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM nhan_than WHERE id = ?", (nhan_than_id,))
    conn.commit()
    conn.close()
    return True

# ============================================
# HÀM XỬ LÝ TÀI LIỆU ĐÍNH KÈM
# ============================================
def get_upload_folder(cccd):
    """Tạo và trả về đường dẫn thư mục upload cho CCCD"""
    base_path = Path(__file__).parent / "uploads" / cccd
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path

def save_tai_lieu(cccd, uploaded_file, loai_tai_lieu, mo_ta=""):
    """Lưu file và metadata vào database"""
    if not uploaded_file:
        return False, "Không có file"
    
    # Kiểm tra dung lượng
    file_size = len(uploaded_file.getvalue())
    if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        return False, f"File quá lớn! Giới hạn {MAX_FILE_SIZE_MB}MB"
    
    # Kiểm tra extension
    file_ext = uploaded_file.name.split('.')[-1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return False, f"Định dạng không hỗ trợ! Chỉ chấp nhận: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Tạo tên file unique
    unique_name = f"{uuid.uuid4().hex[:8]}_{uploaded_file.name}"
    
    # Lưu file vào thư mục
    upload_folder = get_upload_folder(cccd)
    file_path = upload_folder / unique_name
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getvalue())
    
    # Lưu metadata vào database
    duong_dan = f"uploads/{cccd}/{unique_name}"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tai_lieu (cccd, ten_file_goc, ten_file_luu, duong_dan, loai_tai_lieu, mo_ta, dung_luong, dinh_dang)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (cccd, uploaded_file.name, unique_name, duong_dan, loai_tai_lieu, mo_ta, file_size, file_ext))
    conn.commit()
    conn.close()
    
    return True, "Đã upload thành công!"

def get_tai_lieu_by_cccd(cccd):
    """Lấy danh sách tài liệu theo CCCD"""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM tai_lieu WHERE cccd = ? ORDER BY created_at DESC", conn, params=(cccd,))
    conn.close()
    return df

def delete_tai_lieu(tai_lieu_id):
    """Xóa tài liệu (cả file và metadata)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Lấy đường dẫn file trước khi xóa
    cursor.execute("SELECT duong_dan FROM tai_lieu WHERE id = ?", (tai_lieu_id,))
    result = cursor.fetchone()
    
    if result:
        duong_dan = result[0]
        # Xóa file từ disk
        file_path = Path(__file__).parent / duong_dan
        if file_path.exists():
            file_path.unlink()
        
        # Xóa metadata từ database
        cursor.execute("DELETE FROM tai_lieu WHERE id = ?", (tai_lieu_id,))
        conn.commit()
    
    conn.close()
    return True

def get_file_path(tai_lieu_id):
    """Lấy đường dẫn file để download"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT duong_dan, ten_file_goc FROM tai_lieu WHERE id = ?", (tai_lieu_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        file_path = Path(__file__).parent / result[0]
        return file_path, result[1]  # path, original_name
    return None, None

def save_ho_so_dac_thu(cccd, loai_hinh, noi_dung_dict, ghi_chu=""):
    """Lưu hồ sơ đặc thù"""
    if not noi_dung_dict:
        return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ho_so_dac_thu (cccd, loai_hinh, noi_dung_chi_tiet, ghi_chu)
        VALUES (?, ?, ?, ?)
    """, (cccd, loai_hinh, json.dumps(noi_dung_dict, ensure_ascii=False), ghi_chu))
    conn.commit()
    conn.close()

# ============================================
# HÀM TRUY VẤN CHO PROFILE VIEW 360
# ============================================
def get_doi_tuong_detail(cccd):
    """Lấy thông tin chi tiết đối tượng theo CCCD"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM doi_tuong WHERE cccd = ?", (cccd,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def get_lien_he_by_cccd(cccd):
    """Lấy danh sách liên hệ theo CCCD"""
    conn = get_connection()
    query = "SELECT * FROM lien_he WHERE cccd = ? ORDER BY created_at DESC"
    df = pd.read_sql_query(query, conn, params=(cccd,))
    conn.close()
    return df

def get_tai_chinh_by_cccd(cccd):
    """Lấy danh sách tài khoản ngân hàng theo CCCD"""
    conn = get_connection()
    query = "SELECT * FROM tai_chinh WHERE cccd = ? ORDER BY created_at DESC"
    df = pd.read_sql_query(query, conn, params=(cccd,))
    conn.close()
    return df

def get_phuong_tien_by_cccd(cccd):
    """Lấy danh sách phương tiện theo CCCD"""
    conn = get_connection()
    query = "SELECT * FROM phuong_tien WHERE cccd = ? ORDER BY created_at DESC"
    df = pd.read_sql_query(query, conn, params=(cccd,))
    conn.close()
    return df

def get_ho_so_dac_thu_by_cccd(cccd):
    """Lấy danh sách hồ sơ đặc thù theo CCCD"""
    conn = get_connection()
    query = "SELECT * FROM ho_so_dac_thu WHERE cccd = ? ORDER BY created_at DESC"
    df = pd.read_sql_query(query, conn, params=(cccd,))
    conn.close()
    return df

def delete_doi_tuong(cccd):
    """Xóa đối tượng và tất cả dữ liệu liên quan"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Foreign key ON DELETE CASCADE sẽ tự động xóa dữ liệu liên quan
        cursor.execute("DELETE FROM doi_tuong WHERE cccd = ?", (cccd,))
        conn.commit()
        conn.close()
        
        # Xóa thư mục uploads của đối tượng
        upload_folder = Path(__file__).parent / "uploads" / cccd
        if upload_folder.exists():
            shutil.rmtree(upload_folder)
        
        return True, "Đã xóa thành công!"
    except Exception as e:
        conn.close()
        return False, str(e)

def update_doi_tuong(cccd, data):
    """Cập nhật thông tin đối tượng"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE doi_tuong 
            SET ho_ten = ?, ngay_sinh = ?, gioi_tinh = ?, dia_chi_tinh = ?,
                dia_chi_xa = ?, phan_loai_nghe_nghiep = ?, chi_tiet_nghe_nghiep = ?,
                ghi_chu_chung = ?, updated_at = CURRENT_TIMESTAMP
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
            cccd
        ))
        conn.commit()
        conn.close()
        return True, "Cập nhật thành công!"
    except Exception as e:
        conn.close()
        return False, str(e)

# ============================================
# SIDEBAR - ĐIỀU HƯỚNG
# ============================================
with st.sidebar:
    st.markdown("# 🛡️ Security Profile 360")
    st.markdown("---")
    
    # Menu điều hướng với text ngắn gọn
    menu = st.radio(
        "Điều hướng",
        options=["🏠 Dashboard", "📝 Nhập liệu", "📥 Nhập Excel", "🔍 Tra cứu", "🔎 Rà soát"],
        label_visibility="collapsed",
    )
    
    st.markdown("---")
    
    # Thống kê nhanh
    st.markdown("### 📊 Thống kê nhanh")
    stats = get_statistics()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Tổng ĐT", stats["total"])
    with col2:
        dac_thu_total = sum(stats["dac_thu"].values()) if stats["dac_thu"] else 0
        st.metric("Nước ngoài", dac_thu_total)
    
    st.markdown("---")
    
    # Nút sao lưu
    st.markdown("### 💾 Sao lưu")
    db_path = get_db_path()
    if Path(db_path).exists():
        with open(db_path, "rb") as f:
            st.download_button(
                label="📥 Tải file backup",
                data=f.read(),
                file_name=f"security_profile_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.db",
                mime="application/octet-stream",
                use_container_width=True,
            )

# ============================================
# TRANG DASHBOARD
# ============================================
def page_dashboard():
    """Trang Dashboard - Tổng quan hệ thống"""
    import plotly.express as px
    import plotly.graph_objects as go
    
    st.markdown("# 🏠 Dashboard")
    st.markdown("### Tổng quan hệ thống quản lý hồ sơ an ninh")
    
    st.markdown("---")
    
    # Thống kê chính
    stats = get_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📋 Tổng đối tượng",
            value=stats["total"],
        )
    
    with col2:
        nam_count = stats["gioi_tinh"].get("Nam", 0)
        st.metric(
            label="👨 Nam giới",
            value=nam_count,
        )
    
    with col3:
        nu_count = stats["gioi_tinh"].get("Nữ", 0)
        st.metric(
            label="👩 Nữ giới",
            value=nu_count,
        )
    
    with col4:
        dac_thu_total = sum(stats["dac_thu"].values()) if stats["dac_thu"] else 0
        st.metric(
            label="🌐 Yếu tố nước ngoài",
            value=dac_thu_total,
        )
    
    st.markdown("---")
    
    # Row 1: Pie Chart giới tính + Bar chart nghề nghiệp
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("### 👥 Phân bố giới tính")
        if stats["gioi_tinh"] and sum(stats["gioi_tinh"].values()) > 0:
            df_gt = pd.DataFrame(
                list(stats["gioi_tinh"].items()),
                columns=["Giới tính", "Số lượng"]
            )
            fig_pie = px.pie(
                df_gt, 
                values='Số lượng', 
                names='Giới tính',
                color_discrete_sequence=['#667eea', '#764ba2'],
                hole=0.4
            )
            fig_pie.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                margin=dict(t=20, b=20, l=20, r=20),
                showlegend=True,
                legend=dict(font=dict(size=12))
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("💡 Chưa có dữ liệu giới tính.")
    
    with col_right:
        st.markdown("### 📊 Phân loại nghề nghiệp")
        if stats["nghe_nghiep"] and sum(stats["nghe_nghiep"].values()) > 0:
            df_nghe = pd.DataFrame(
                list(stats["nghe_nghiep"].items()),
                columns=["Phân loại", "Số lượng"]
            )
            fig_bar = px.bar(
                df_nghe, 
                x='Phân loại', 
                y='Số lượng',
                color='Phân loại',
                color_discrete_sequence=['#667eea', '#764ba2', '#00d9a5', '#ffc107']
            )
            fig_bar.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                margin=dict(t=20, b=20, l=20, r=20),
                showlegend=False,
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("💡 Chưa có dữ liệu nghề nghiệp.")
    
    st.markdown("---")
    
    # Row 2: Hồ sơ đặc thù + Top xã/phường
    col_left2, col_right2 = st.columns(2)
    
    with col_left2:
        st.markdown("### 🌐 Hồ sơ đặc thù CSXH")
        if stats["dac_thu"] and sum(stats["dac_thu"].values()) > 0:
            df_dac_thu = pd.DataFrame(
                [(LOAI_HINH_DAC_THU.get(k, k), v) for k, v in stats["dac_thu"].items()],
                columns=["Loại hình", "Số lượng"]
            )
            fig_dac_thu = px.bar(
                df_dac_thu, 
                y='Loại hình', 
                x='Số lượng',
                orientation='h',
                color='Loại hình',
                color_discrete_sequence=['#ff6b6b', '#ffc107', '#00d9a5', '#667eea', '#764ba2']
            )
            fig_dac_thu.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                margin=dict(t=20, b=20, l=20, r=20),
                showlegend=False,
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
            )
            st.plotly_chart(fig_dac_thu, use_container_width=True)
        else:
            st.info("💡 Chưa có hồ sơ đặc thù nào.")
    
    with col_right2:
        st.markdown("### 🏘️ Top 10 xã/phường")
        # Lấy thống kê theo xã/phường
        conn = get_connection()
        query = """
            SELECT dia_chi_xa, COUNT(*) as so_luong 
            FROM doi_tuong 
            WHERE dia_chi_xa IS NOT NULL AND dia_chi_xa != ''
            GROUP BY dia_chi_xa 
            ORDER BY so_luong DESC 
            LIMIT 10
        """
        df_xa = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df_xa.empty:
            fig_xa = px.bar(
                df_xa, 
                y='dia_chi_xa', 
                x='so_luong',
                orientation='h',
                color='so_luong',
                color_continuous_scale='Viridis'
            )
            fig_xa.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                margin=dict(t=20, b=20, l=20, r=20),
                showlegend=False,
                coloraxis_showscale=False,
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)', title='Số lượng'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)', title='Xã/Phường')
            )
            st.plotly_chart(fig_xa, use_container_width=True)
        else:
            st.info("💡 Chưa có dữ liệu phân bố theo xã/phường.")
    
    st.markdown("---")
    
    # Bản ghi gần đây
    st.markdown("### 📋 Hồ sơ được thêm gần đây")
    recent_df = get_recent_records(10)
    if not recent_df.empty:
        # Đổi tên cột cho dễ đọc
        recent_df.columns = ["CCCD", "Họ tên", "Ngày sinh", "Giới tính", "Xã/Phường", "Phân loại"]
        st.dataframe(recent_df, use_container_width=True, hide_index=True)
    else:
        st.info("💡 Chưa có hồ sơ nào. Bấm vào **📝 Nhập liệu** để thêm mới.")

# ============================================
# TRANG NHẬP LIỆU
# ============================================
def page_nhap_lieu():
    """Trang Nhập liệu - Form thêm mới đối tượng"""
    st.markdown("# 📝 Nhập liệu")
    st.markdown("### Thêm mới hồ sơ đối tượng")
    
    st.markdown("---")
    
    # Tabs cho các phần nhập liệu
    tab1, tab_nhan_than, tab2, tab3, tab_tai_lieu = st.tabs([
        "👤 Thông tin cá nhân",
        "👨‍👩‍👧‍👦 Thân nhân",
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
            
            # Ngày sinh với format dd/mm/yyyy
            ngay_sinh_str = st.text_input(
                "Ngày sinh (dd/mm/yyyy)",
                placeholder="01/01/1990",
                help="Nhập ngày sinh theo định dạng dd/mm/yyyy"
            )
            
            # Parse ngày sinh
            ngay_sinh = None
            if ngay_sinh_str:
                try:
                    ngay_sinh = datetime.strptime(ngay_sinh_str, "%d/%m/%Y").date()
                except ValueError:
                    st.error("⚠️ Định dạng ngày không hợp lệ! Vui lòng nhập dd/mm/yyyy")
            
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
                        'ghi_chu_chung': ghi_chu
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
                            st.success(f"✅ Đã xóa {row['loai_quan_he']}: {row['ho_ten']}")
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
                    st.success(f"✅ Đã thêm {loai_quan_he}: {nt_ho_ten}")
                    st.rerun()
                else:
                    st.error("⚠️ CCCD không tồn tại trong hệ thống!")
            else:
                st.warning("⚠️ Vui lòng nhập họ tên thân nhân!")
    
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
                        st.success(f"✅ Đã thêm {loai_lien_he}: {gia_tri_lien_he}")
                    else:
                        st.error("⚠️ CCCD không tồn tại trong hệ thống!")
                else:
                    st.warning("⚠️ Vui lòng nhập đầy đủ thông tin!")
        
        with col2:
            st.markdown("##### 🏦 Tài khoản ngân hàng")
            
            ngan_hang = st.selectbox("Ngân hàng", DANH_SACH_NGAN_HANG, key="ngan_hang_tab2")
            so_tai_khoan = st.text_input("Số tài khoản", placeholder="1234567890")
            chu_tai_khoan = st.text_input("Chủ tài khoản", placeholder="NGUYEN VAN A")
            
            if st.button("💾 Lưu tài khoản", use_container_width=True, type="primary"):
                if current_cccd and so_tai_khoan:
                    if check_cccd_exists(current_cccd):
                        save_tai_chinh(current_cccd, ngan_hang, so_tai_khoan, chu_tai_khoan)
                        st.success(f"✅ Đã thêm TK {ngan_hang}: {so_tai_khoan}")
                    else:
                        st.error("⚠️ CCCD không tồn tại trong hệ thống!")
                else:
                    st.warning("⚠️ Vui lòng nhập đầy đủ thông tin!")
        
        st.markdown("---")
        
        st.markdown("##### 🚗 Phương tiện giao thông")
        
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
                    st.success(f"✅ Đã thêm xe {loai_xe}: {bien_so}")
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
                noi_dung_dict["thoi_gian"] = st.text_input("Thời gian vi phạm", key="vp_tg")
                noi_dung_dict["hinh_thuc_xu_ly"] = st.text_input("Hình thức xử lý", key="vp_ht")
            noi_dung_dict["noi_dung_vp"] = st.text_area("Nội dung vi phạm", key="vp_nd", height=100)
            
        elif loai_hinh == "Xac_Minh":
            st.markdown("##### 🔍 Thông tin xác minh")
            col1, col2 = st.columns(2)
            with col1:
                noi_dung_dict["co_quan_xm"] = st.text_input("Cơ quan xác minh", key="xm_cq")
                noi_dung_dict["thoi_gian"] = st.text_input("Thời gian xác minh", key="xm_tg")
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
                        st.success(f"✅ Đã lưu hồ sơ đặc thù: {LOAI_HINH_DAC_THU[loai_hinh]}")
                        st.balloons()
                    else:
                        st.warning("⚠️ Vui lòng nhập ít nhất một thông tin!")
                else:
                    st.error("⚠️ CCCD không tồn tại trong hệ thống! Vui lòng thêm thông tin cá nhân trước.")
            else:
                st.error("⚠️ Vui lòng nhập CCCD!")
    
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
                            st.success(f"✅ Đã xóa: {row['ten_file_goc']}")
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
                        st.success(f"✅ {message}: {uploaded_file.name}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("⚠️ CCCD không tồn tại trong hệ thống!")
            else:
                st.warning("⚠️ Vui lòng chọn file để upload!")


# ============================================
# TRANG NHẬP EXCEL (BULK IMPORT)
# ============================================
def page_nhap_excel():
    """Trang Nhập Excel - Import dữ liệu hàng loạt từ file Excel 5 sheet"""
    st.markdown("# 📥 Nhập Excel")
    st.markdown("### Import dữ liệu hàng loạt từ file Excel đa sheet")
    
    st.markdown("---")
    
    # ===== BƯỚC 1: TẢI FILE MẪU =====
    st.markdown("#### 📄 Bước 1: Tải file mẫu")
    st.info("""
    **File mẫu gồm 5 sheet:**
    - **Sheet 1 - Đối tượng**: Thông tin cơ bản (CCCD, Họ tên, Ngày sinh...)
    - **Sheet 2 - Liên hệ**: SĐT, Email, Facebook, Zalo...
    - **Sheet 3 - Tài chính**: Tài khoản ngân hàng
    - **Sheet 4 - Phương tiện**: Xe cộ
    - **Sheet 5 - Hồ sơ CSXH**: Theo loại hình bạn chọn bên dưới
    """)
    
    # Chọn loại CSXH
    st.markdown("**Chọn loại Hồ sơ CSXH cho Sheet 5:**")
    loai_csxh_options = {
        "Tổng hợp (tất cả loại)": None,
        "🤵 Hôn nhân với người nước ngoài": "Hon_Nhan_NN",
        "🏢 Làm việc cho tổ chức nước ngoài": "Lam_Viec_NN",
        "🎓 Du học/Công tác nước ngoài": "Hoc_Tap_Cong_Tac_NN",
        "⚠️ Vi phạm pháp luật ở nước ngoài": "Vi_Pham_NN",
        "🔍 Đã từng được xác minh": "Xac_Minh",
    }
    
    selected_csxh_label = st.selectbox(
        "Loại Hồ sơ CSXH",
        list(loai_csxh_options.keys()),
        help="Chọn loại để file mẫu có các cột chi tiết phù hợp"
    )
    selected_csxh = loai_csxh_options[selected_csxh_label]
    
    # Nút tải file mẫu
    template_data = create_excel_template(loai_csxh=selected_csxh)
    
    # Tạo tên file đơn giản (không có ký tự đặc biệt)
    if selected_csxh:
        file_name = f"mau_{selected_csxh}.xlsx"
    else:
        file_name = "mau_tonghop.xlsx"
    
    st.download_button(
        label=f"📥 Tải file mẫu: {selected_csxh_label}",
        data=template_data,
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        key=f"download_{selected_csxh or 'all'}"
    )
    
    st.markdown("---")
    
    # ===== BƯỚC 2: UPLOAD FILE =====
    st.markdown("#### 📤 Bước 2: Upload file Excel đã điền")
    
    uploaded_file = st.file_uploader(
        "Chọn file Excel",
        type=["xlsx", "xls"],
        help="File Excel phải có đủ 5 sheet theo đúng định dạng file mẫu"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ Đã tải lên: **{uploaded_file.name}**")
        
        st.markdown("---")
        
        # ===== BƯỚC 3: VALIDATE & PREVIEW =====
        st.markdown("#### 🔍 Bước 3: Kiểm tra dữ liệu")
        
        with st.spinner("Đang đọc và kiểm tra dữ liệu..."):
            validation_results = validate_excel_data(uploaded_file)
        
        # Tổng kết validate
        total_valid = sum(r['valid_count'] for r in validation_results.values())
        total_errors = sum(len(r['errors']) for r in validation_results.values())
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("✅ Bản ghi hợp lệ", total_valid)
        with col2:
            st.metric("❌ Lỗi phát hiện", total_errors)
        
        # Nút tải file lỗi nếu có lỗi
        if total_errors > 0:
            error_excel = export_error_excel(validation_results)
            if error_excel:
                st.download_button(
                    label="📥 Tải file các dòng lỗi để sửa",
                    data=error_excel,
                    file_name="loi_can_sua.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="secondary",
                    help="File Excel chứa các dòng lỗi với cột LY_DO_LOI giải thích lý do"
                )
        
        # Chi tiết từng sheet
        st.markdown("---")
        
        tab_dt, tab_lh, tab_tc, tab_pt, tab_hs = st.tabs([
            f"👤 Đối tượng ({validation_results['doi_tuong']['valid_count']})",
            f"📞 Liên hệ ({validation_results['lien_he']['valid_count']})",
            f"💳 Tài chính ({validation_results['tai_chinh']['valid_count']})",
            f"🚗 Phương tiện ({validation_results['phuong_tien']['valid_count']})",
            f"🌐 Hồ sơ CSXH ({validation_results['ho_so_dac_thu']['valid_count']})"
        ])
        
        with tab_dt:
            if validation_results['doi_tuong']['errors']:
                with st.expander(f"⚠️ {len(validation_results['doi_tuong']['errors'])} lỗi", expanded=True):
                    for err in validation_results['doi_tuong']['errors'][:10]:
                        st.error(err)
                    if len(validation_results['doi_tuong']['errors']) > 10:
                        st.warning(f"... và {len(validation_results['doi_tuong']['errors']) - 10} lỗi khác")
            
            if validation_results['doi_tuong']['data'] is not None:
                st.dataframe(validation_results['doi_tuong']['data'], use_container_width=True)
            else:
                st.info("Không có dữ liệu hợp lệ")
        
        with tab_lh:
            if validation_results['lien_he']['errors']:
                with st.expander(f"⚠️ {len(validation_results['lien_he']['errors'])} lỗi"):
                    for err in validation_results['lien_he']['errors'][:10]:
                        st.error(err)
            if validation_results['lien_he']['data'] is not None:
                st.dataframe(validation_results['lien_he']['data'], use_container_width=True)
            else:
                st.info("Không có dữ liệu hoặc sheet trống")
        
        with tab_tc:
            if validation_results['tai_chinh']['errors']:
                with st.expander(f"⚠️ {len(validation_results['tai_chinh']['errors'])} lỗi"):
                    for err in validation_results['tai_chinh']['errors'][:10]:
                        st.error(err)
            if validation_results['tai_chinh']['data'] is not None:
                st.dataframe(validation_results['tai_chinh']['data'], use_container_width=True)
            else:
                st.info("Không có dữ liệu hoặc sheet trống")
        
        with tab_pt:
            if validation_results['phuong_tien']['errors']:
                with st.expander(f"⚠️ {len(validation_results['phuong_tien']['errors'])} lỗi"):
                    for err in validation_results['phuong_tien']['errors'][:10]:
                        st.error(err)
            if validation_results['phuong_tien']['data'] is not None:
                st.dataframe(validation_results['phuong_tien']['data'], use_container_width=True)
            else:
                st.info("Không có dữ liệu hoặc sheet trống")
        
        with tab_hs:
            if validation_results['ho_so_dac_thu']['errors']:
                with st.expander(f"⚠️ {len(validation_results['ho_so_dac_thu']['errors'])} lỗi"):
                    for err in validation_results['ho_so_dac_thu']['errors'][:10]:
                        st.error(err)
            if validation_results['ho_so_dac_thu']['data'] is not None:
                st.dataframe(validation_results['ho_so_dac_thu']['data'], use_container_width=True)
            else:
                st.info("Không có dữ liệu hoặc sheet trống")
        
        # ===== BƯỚC 4: IMPORT =====
        st.markdown("---")
        st.markdown("#### 💾 Bước 4: Import vào Database")
        
        if total_valid > 0:
            st.warning(f"""
            **Sẵn sàng import {total_valid} bản ghi hợp lệ:**
            - 👤 Đối tượng: {validation_results['doi_tuong']['valid_count']}
            - 📞 Liên hệ: {validation_results['lien_he']['valid_count']}
            - 💳 Tài chính: {validation_results['tai_chinh']['valid_count']}
            - 🚗 Phương tiện: {validation_results['phuong_tien']['valid_count']}
            - 🌐 Hồ sơ đặc thù: {validation_results['ho_so_dac_thu']['valid_count']}
            
            ⚠️ **Lưu ý**: Nếu có lỗi trong quá trình import, toàn bộ dữ liệu sẽ được rollback.
            """)
            
            if st.button("🚀 Import vào Database", type="primary", use_container_width=True):
                with st.spinner("Đang import dữ liệu..."):
                    success, message, stats = bulk_import_all(validation_results)
                
                if success:
                    st.success(message)
                    st.balloons()
                    
                    # Hiển thị chi tiết
                    st.markdown("**Chi tiết:**")
                    col1, col2, col3, col4, col5 = st.columns(5)
                    col1.metric("👤 Đối tượng", stats['doi_tuong'])
                    col2.metric("📞 Liên hệ", stats['lien_he'])
                    col3.metric("💳 Tài chính", stats['tai_chinh'])
                    col4.metric("🚗 Phương tiện", stats['phuong_tien'])
                    col5.metric("🌐 Đặc thù", stats['ho_so_dac_thu'])
                else:
                    st.error(message)
                    st.warning("⚠️ Đã rollback toàn bộ dữ liệu do lỗi. Vui lòng kiểm tra lại file Excel.")
        else:
            st.error("❌ Không có dữ liệu hợp lệ để import. Vui lòng sửa lỗi và thử lại.")

# ============================================
# TRANG TRA CỨU
# ============================================
def page_tra_cuu():
    """Trang Tra cứu - Tìm kiếm đối tượng"""
    st.markdown("# 🔍 Tra cứu")
    st.markdown("### Tìm kiếm và tra cứu hồ sơ đối tượng")
    
    st.markdown("---")
    
    # Thanh tìm kiếm
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        search_query = st.text_input(
            "Tìm kiếm",
            placeholder="Nhập CCCD, họ tên để tìm kiếm...",
            label_visibility="collapsed"
        )
    
    with col2:
        search_type = st.selectbox(
            "Loại",
            ["Tất cả", "CCCD", "Họ tên"],
            label_visibility="collapsed"
        )
    
    with col3:
        search_clicked = st.button("🔍 Tìm kiếm", type="primary", use_container_width=True)
    
    st.markdown("---")
    
    # Bộ lọc nâng cao
    with st.expander("🎛️ Bộ lọc nâng cao", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_tinh = st.selectbox("Tỉnh/TP", ["Tất cả"] + TINH_OPTIONS)
        with col2:
            filter_gioi_tinh = st.selectbox("Giới tính", ["Tất cả"] + GIOI_TINH_OPTIONS)
        with col3:
            filter_dac_thu = st.selectbox(
                "Yếu tố đặc thù",
                ["Tất cả"] + list(LOAI_HINH_DAC_THU.values())
            )
    
    st.markdown("---")
    
    # Thực hiện tìm kiếm
    st.markdown("### 📋 Kết quả")
    
    conn = get_connection()
    
    if search_clicked and search_query:
        # Tìm kiếm theo query
        if search_type == "CCCD":
            query = "SELECT * FROM doi_tuong WHERE cccd LIKE ?"
            params = (f"%{search_query}%",)
        elif search_type == "Họ tên":
            query = "SELECT * FROM doi_tuong WHERE ho_ten LIKE ?"
            params = (f"%{search_query}%",)
        else:
            query = "SELECT * FROM doi_tuong WHERE cccd LIKE ? OR ho_ten LIKE ?"
            params = (f"%{search_query}%", f"%{search_query}%")
        
        df = pd.read_sql_query(query, conn, params=params)
        st.info(f"🔍 Tìm thấy **{len(df)}** kết quả cho: '{search_query}'")
    else:
        # Hiển thị tất cả (giới hạn 100)
        query = "SELECT cccd, ho_ten, ngay_sinh, gioi_tinh, dia_chi_xa, phan_loai_nghe_nghiep FROM doi_tuong ORDER BY created_at DESC LIMIT 100"
        df = pd.read_sql_query(query, conn)
    
    conn.close()
    
    if not df.empty:
        # Đổi tên cột
        display_df = df.copy()
        if 'cccd' in display_df.columns:
            col_map = {
                'cccd': 'CCCD',
                'ho_ten': 'Họ tên',
                'ngay_sinh': 'Ngày sinh',
                'gioi_tinh': 'Giới tính',
                'dia_chi_xa': 'Xã/Phường',
                'phan_loai_nghe_nghiep': 'Phân loại',
                'dia_chi_tinh': 'Tỉnh/TP',
                'chi_tiet_nghe_nghiep': 'Nơi làm việc',
                'ghi_chu_chung': 'Ghi chú'
            }
            display_df = display_df.rename(columns={k: v for k, v in col_map.items() if k in display_df.columns})
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Chọn và xem hồ sơ chi tiết
        st.markdown("##### 👤 Xem hồ sơ chi tiết")
        col_select, col_btn = st.columns([3, 1])
        
        with col_select:
            # Tạo danh sách options: CCCD - Họ tên
            cccd_col = 'cccd' if 'cccd' in df.columns else 'CCCD'
            hoten_col = 'ho_ten' if 'ho_ten' in df.columns else 'Họ tên'
            options = [f"{row[cccd_col]} - {row[hoten_col]}" for _, row in df.iterrows()]
            selected = st.selectbox("Chọn đối tượng", options, key="select_profile")
        
        with col_btn:
            if st.button("👁️ Xem hồ sơ", type="primary", use_container_width=True):
                if selected:
                    selected_cccd = selected.split(" - ")[0]
                    st.session_state.view_profile_cccd = selected_cccd
                    st.rerun()
        
        st.markdown("---")
        
        # Nút xuất Excel
        st.download_button(
            label="📥 Xuất Excel",
            data=df.to_csv(index=False).encode('utf-8-sig'),
            file_name=f"danh_sach_doi_tuong_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
    else:
        st.info("💡 Không có dữ liệu. Hãy thêm đối tượng mới trong phần **📝 Nhập liệu**.")

# ============================================
# TRANG HỒ SƠ CHI TIẾT (PROFILE VIEW 360)
# ============================================

# Mapping labels tiếng Việt cho các trường CSXH
CSXH_FIELD_LABELS = {
    # Hôn nhân NN
    'ten_doi_tac': 'Tên đối tác',
    'quoc_tich': 'Quốc tịch',
    'so_ho_chieu': 'Số hộ chiếu',
    'tinh_trang': 'Tình trạng',
    # Làm việc NN
    'ten_to_chuc': 'Tên tổ chức',
    'chuc_vu': 'Chức vụ',
    'thoi_gian': 'Thời gian',
    'dia_diem': 'Địa điểm',
    # Du học/Công tác NN
    'dien_di': 'Diện đi',
    'quoc_gia': 'Quốc gia',
    'thoi_gian_di': 'Thời gian đi',
    'thoi_gian_ve': 'Thời gian về',
    'nghe_sau_ve': 'Nghề sau khi về',
    # Vi phạm NN
    'co_quan_bat': 'Cơ quan bắt giữ',
    'hinh_thuc_xu_ly': 'Hình thức xử lý',
    'noi_dung_vp': 'Nội dung vi phạm',
    # Xác minh
    'co_quan_xm': 'Cơ quan xác minh',
    'ket_qua': 'Kết quả',
    'noi_dung_xm': 'Nội dung xác minh',
}

def page_profile_view(cccd):
    """Trang xem chi tiết hồ sơ đối tượng 360 độ"""
    
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
        # Avatar placeholder
        st.markdown("""
        <div style="width: 120px; height: 120px; background: linear-gradient(135deg, #667eea, #764ba2); 
                    border-radius: 50%; display: flex; align-items: center; justify-content: center;
                    font-size: 48px; color: white; margin: 0 auto;">
            👤
        </div>
        """, unsafe_allow_html=True)
    
    with col_header2:
        st.markdown(f"## {doi_tuong.get('ho_ten', 'N/A')}")
        st.markdown(f"**CCCD:** `{cccd}`")
        
        # Tính tuổi
        if doi_tuong.get('ngay_sinh'):
            try:
                ngay_sinh = datetime.strptime(str(doi_tuong['ngay_sinh']), '%Y-%m-%d')
                tuoi = (datetime.now() - ngay_sinh).days // 365
                st.markdown(f"**Ngày sinh:** {ngay_sinh.strftime('%d/%m/%Y')} ({tuoi} tuổi)")
            except:
                st.markdown(f"**Ngày sinh:** {doi_tuong.get('ngay_sinh', 'N/A')}")
        
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
        st.warning(f"⚠️ Bạn có chắc muốn xóa hồ sơ **{doi_tuong.get('ho_ten')}** không? Hành động này không thể hoàn tác!")
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
    tab1, tab_nt, tab2, tab3, tab_tl = st.tabs([
        "📋 Thông tin cá nhân",
        "👨‍👩‍👧‍👦 Thân nhân",
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
                    edit_ho_ten = st.text_input(
                        "Họ và tên *", 
                        value=doi_tuong.get('ho_ten', ''),
                        key="edit_ho_ten"
                    )
                    
                    # Ngày sinh
                    current_ngay_sinh = doi_tuong.get('ngay_sinh', '')
                    if current_ngay_sinh:
                        try:
                            ns_date = datetime.strptime(str(current_ngay_sinh), '%Y-%m-%d').date()
                            edit_ngay_sinh_str = ns_date.strftime('%d/%m/%Y')
                        except:
                            edit_ngay_sinh_str = ''
                    else:
                        edit_ngay_sinh_str = ''
                    
                    edit_ngay_sinh_input = st.text_input(
                        "Ngày sinh (dd/mm/yyyy)",
                        value=edit_ngay_sinh_str,
                        key="edit_ngay_sinh"
                    )
                    
                    edit_gioi_tinh = st.selectbox(
                        "Giới tính",
                        GIOI_TINH_OPTIONS,
                        index=GIOI_TINH_OPTIONS.index(doi_tuong.get('gioi_tinh', 'Nam')) if doi_tuong.get('gioi_tinh') in GIOI_TINH_OPTIONS else 0,
                        key="edit_gioi_tinh"
                    )
                
                with col2:
                    edit_dia_chi_tinh = st.selectbox(
                        "Tỉnh/TP",
                        TINH_OPTIONS,
                        index=TINH_OPTIONS.index(doi_tuong.get('dia_chi_tinh', 'Phú Thọ')) if doi_tuong.get('dia_chi_tinh') in TINH_OPTIONS else 0,
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
                        index=PHAN_LOAI_NGHE_NGHIEP_OPTIONS.index(doi_tuong.get('phan_loai_nghe_nghiep', 'Lao động tự do')) if doi_tuong.get('phan_loai_nghe_nghiep') in PHAN_LOAI_NGHE_NGHIEP_OPTIONS else 0,
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
                    submitted = st.form_submit_button("💾 Lưu thay đổi", type="primary", use_container_width=True)
                with col_btn2:
                    cancel = st.form_submit_button("❌ Hủy", use_container_width=True)
                
                if submitted:
                    # Validate
                    if not edit_ho_ten:
                        st.error("⚠️ Vui lòng nhập họ tên!")
                    else:
                        # Parse ngày sinh
                        edit_ngay_sinh = None
                        if edit_ngay_sinh_input:
                            try:
                                edit_ngay_sinh = datetime.strptime(edit_ngay_sinh_input, "%d/%m/%Y").strftime('%Y-%m-%d')
                            except ValueError:
                                st.error("⚠️ Định dạng ngày không hợp lệ! Vui lòng nhập dd/mm/yyyy")
                                st.stop()
                        
                        update_data = {
                            'ho_ten': edit_ho_ten,
                            'ngay_sinh': edit_ngay_sinh,
                            'gioi_tinh': edit_gioi_tinh,
                            'dia_chi_tinh': edit_dia_chi_tinh,
                            'dia_chi_xa': edit_dia_chi_xa,
                            'phan_loai_nghe_nghiep': edit_phan_loai,
                            'chi_tiet_nghe_nghiep': edit_chi_tiet_nghe,
                            'ghi_chu_chung': edit_ghi_chu
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
                st.markdown(f"**Địa chỉ:** {doi_tuong.get('dia_chi_xa', '')} - {doi_tuong.get('dia_chi_tinh', '')}")
                st.markdown(f"**Phân loại nghề nghiệp:** {doi_tuong.get('phan_loai_nghe_nghiep', 'N/A')}")
            
            with col2:
                st.markdown(f"**Chi tiết nơi làm việc:** {doi_tuong.get('chi_tiet_nghe_nghiep', 'N/A')}")
                st.markdown(f"**Ngày tạo:** {doi_tuong.get('created_at', 'N/A')}")
            
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
                    if st.button("🗑️", key=f"del_nt_{row['id']}", help=f"Xóa {row['ho_ten']}"):
                        delete_nhan_than(row['id'])
                        st.success(f"✅ Đã xóa {row['loai_quan_he']}: {row['ho_ten']}")
                        st.rerun()
            st.markdown("---")
        else:
            st.info("💡 Chưa có thông tin thân nhân. Nhấn **➕ Thêm thân nhân mới** để thêm.")
        
        # Form thêm thân nhân mới
        with st.expander("➕ Thêm thân nhân mới", expanded=False):
            with st.form("add_nhan_than_profile_form"):
                nt_loai_quan_he = st.selectbox(
                    "Loại quan hệ",
                    ["Bố đẻ", "Mẹ đẻ", "Vợ/Chồng", "Anh/Chị em ruột", "Anh/Chị em họ", "Ông/Bà", "Con", "Bạn thân", "Đồng nghiệp", "Khác"],
                    key="pv_nt_loai"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    nt_ho_ten = st.text_input("Họ và tên *", key="pv_nt_ho_ten")
                    nt_cccd_nt = st.text_input("Số CCCD (nếu có)", key="pv_nt_cccd")
                    nt_ngay_sinh = st.date_input("Ngày sinh", value=None, key="pv_nt_ngay_sinh", format="DD/MM/YYYY", min_value=date(1900, 1, 1), max_value=date(2100, 12, 31))
                with col2:
                    nt_phan_loai_nghe = st.selectbox("Phân loại nghề nghiệp", PHAN_LOAI_NGHE_NGHIEP_OPTIONS, key="pv_nt_phan_loai")
                    nt_nghe_nghiep = st.text_input("Chi tiết nghề nghiệp", placeholder="Ví dụ: Giáo viên THPT, Nông dân...", key="pv_nt_nghe")
                    nt_noi_o = st.text_input("Nơi ở hiện nay", key="pv_nt_noi_o")
                
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
                            ngay_sinh=nt_ngay_sinh.strftime('%Y-%m-%d') if nt_ngay_sinh else None,
                            nghe_nghiep=nghe_nghiep_full,
                            noi_o=nt_noi_o,
                            ghi_chu=nt_ghi_chu
                        )
                        st.success(f"✅ Đã thêm {nt_loai_quan_he}: {nt_ho_ten}")
                        st.rerun()
                    else:
                        st.warning("⚠️ Vui lòng nhập họ tên!")
    
    with tab2:
        st.markdown("#### 📞 Liên hệ & Tài sản")
        
        # ========== LIÊN HỆ ==========
        st.markdown("##### 📱 Thông tin liên hệ")
        df_lien_he = get_lien_he_by_cccd(cccd)
        if not df_lien_he.empty:
            display_cols = ['loai_lien_he', 'gia_tri', 'ghi_chu', 'created_at']
            display_df = df_lien_he[display_cols].rename(columns={
                'loai_lien_he': 'Loại', 'gia_tri': 'Giá trị', 'ghi_chu': 'Ghi chú', 'created_at': 'Ngày tạo'
            })
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("💡 Chưa có thông tin liên hệ")
        
        # Form thêm liên hệ
        with st.expander("➕ Thêm liên hệ mới", expanded=False):
            with st.form("add_lien_he_form"):
                col1, col2 = st.columns(2)
                with col1:
                    lh_loai = st.selectbox("Loại liên hệ", LOAI_LIEN_HE_OPTIONS, key="add_lh_loai")
                    lh_gia_tri = st.text_input("Giá trị (SĐT/Email/Link...)", key="add_lh_gia_tri")
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
            display_cols = ['ngan_hang', 'so_tai_khoan', 'chu_tai_khoan', 'ghi_chu']
            display_df = df_tai_chinh[display_cols].rename(columns={
                'ngan_hang': 'Ngân hàng', 'so_tai_khoan': 'Số TK', 'chu_tai_khoan': 'Chủ TK', 'ghi_chu': 'Ghi chú'
            })
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("💡 Chưa có thông tin tài khoản ngân hàng")
        
        # Form thêm tài khoản
        with st.expander("➕ Thêm tài khoản ngân hàng", expanded=False):
            with st.form("add_tai_chinh_form"):
                col1, col2 = st.columns(2)
                with col1:
                    tc_ngan_hang = st.selectbox("Ngân hàng", DANH_SACH_NGAN_HANG, key="add_tc_ngan_hang")
                    tc_so_tk = st.text_input("Số tài khoản", key="add_tc_so_tk")
                with col2:
                    tc_chu_tk = st.text_input("Chủ tài khoản", key="add_tc_chu_tk")
                    tc_ghi_chu = st.text_input("Ghi chú", key="add_tc_ghi_chu")
                
                if st.form_submit_button("💾 Lưu tài khoản", type="primary"):
                    if tc_so_tk:
                        save_tai_chinh(cccd, tc_ngan_hang, tc_so_tk, tc_chu_tk, tc_ghi_chu)
                        st.success("✅ Đã thêm tài khoản!")
                        st.rerun()
                    else:
                        st.warning("⚠️ Vui lòng nhập số tài khoản!")
        
        st.markdown("---")
        
        # ========== PHƯƠNG TIỆN ==========
        st.markdown("##### 🚗 Phương tiện")
        df_phuong_tien = get_phuong_tien_by_cccd(cccd)
        if not df_phuong_tien.empty:
            display_cols = ['loai_xe', 'bien_kiem_soat', 'ten_phuong_tien', 'ghi_chu']
            display_df = df_phuong_tien[display_cols].rename(columns={
                'loai_xe': 'Loại xe', 'bien_kiem_soat': 'Biển số', 'ten_phuong_tien': 'Tên xe', 'ghi_chu': 'Ghi chú'
            })
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("💡 Chưa có thông tin phương tiện")
        
        # Form thêm phương tiện
        with st.expander("➕ Thêm phương tiện", expanded=False):
            with st.form("add_phuong_tien_form"):
                col1, col2 = st.columns(2)
                with col1:
                    pt_loai = st.selectbox("Loại xe", LOAI_XE_OPTIONS, key="add_pt_loai")
                    pt_bien_so = st.text_input("Biển kiểm soát", key="add_pt_bien_so")
                with col2:
                    pt_ten = st.text_input("Tên phương tiện", key="add_pt_ten")
                    pt_ghi_chu = st.text_input("Ghi chú", key="add_pt_ghi_chu")
                
                if st.form_submit_button("💾 Lưu phương tiện", type="primary"):
                    if pt_bien_so:
                        save_phuong_tien(cccd, pt_loai, pt_bien_so, pt_ten, pt_ghi_chu)
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
                        noi_dung = json.loads(row['noi_dung_chi_tiet']) if row['noi_dung_chi_tiet'] else {}
                    except:
                        noi_dung = {}
                    
                    col1, col2 = st.columns(2)
                    items = list(noi_dung.items())
                    mid = len(items) // 2 + len(items) % 2
                    
                    with col1:
                        for key, value in items[:mid]:
                            if value:
                                label = CSXH_FIELD_LABELS.get(key, key.replace('_', ' ').title())
                                st.markdown(f"**{label}:** {value}")
                    
                    with col2:
                        for key, value in items[mid:]:
                            if value:
                                label = CSXH_FIELD_LABELS.get(key, key.replace('_', ' ').title())
                                st.markdown(f"**{label}:** {value}")
                    
                    if row.get('ghi_chu'):
                        st.markdown(f"**Ghi chú:** {row['ghi_chu']}")
                    
                    st.caption(f"📅 Ngày tạo: {row.get('created_at', 'N/A')}")
        else:
            st.info("💡 Chưa có hồ sơ đặc thù nào")
    
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
                    if st.button("🗑️", key=f"pv_del_tl_{row['id']}", help=f"Xóa {row['ten_file_goc']}"):
                        delete_tai_lieu(row['id'])
                        st.success(f"✅ Đã xóa: {row['ten_file_goc']}")
                        st.rerun()
            st.markdown("---")
        else:
            st.info("💡 Chưa có tài liệu đính kèm")
        
        # Form upload tài liệu mới
        with st.expander("➕ Upload tài liệu mới", expanded=False):
            st.caption(f"📌 Định dạng hỗ trợ: {', '.join(ALLOWED_EXTENSIONS)} | Giới hạn: {MAX_FILE_SIZE_MB}MB/file")
            
            with st.form("pv_upload_tai_lieu_form"):
                uploaded_file = st.file_uploader(
                    "Chọn file",
                    type=ALLOWED_EXTENSIONS,
                    key="pv_upload_tai_lieu"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    loai_tai_lieu = st.selectbox("Loại tài liệu", LOAI_TAI_LIEU_OPTIONS, key="pv_tl_loai")
                with col2:
                    mo_ta_tl = st.text_input("Mô tả (tùy chọn)", key="pv_tl_mo_ta")
                
                if st.form_submit_button("💾 Upload", type="primary"):
                    if uploaded_file:
                        success, message = save_tai_lieu(cccd, uploaded_file, loai_tai_lieu, mo_ta_tl)
                        if success:
                            st.success(f"✅ {message}: {uploaded_file.name}")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                    else:
                        st.warning("⚠️ Vui lòng chọn file để upload!")

# ============================================
# TRANG RÀ SOÁT HÀNG LOẠT (BATCH SCREENING)
# ============================================
def page_ra_soat():
    """Trang Rà soát - Kiểm tra danh sách hàng loạt với fuzzy matching"""
    st.markdown("# 🔎 Rà soát hàng loạt")
    st.markdown("### Kiểm tra danh sách nhân sự với cơ sở dữ liệu")
    
    st.markdown("---")
    
    st.info("""
    **Tính năng rà soát cho phép:**
    - Upload file Excel danh sách cần kiểm tra
    - Hoặc nhập danh sách CCCD/Họ tên trực tiếp
    - Hệ thống sẽ đối sánh với database và hiển thị kết quả
    """)
    
    # Tab cho 2 cách nhập
    tab_upload, tab_paste = st.tabs(["📥 Upload Excel", "📝 Nhập trực tiếp"])
    
    with tab_upload:
        st.markdown("#### 📥 Upload file Excel")
        uploaded_file = st.file_uploader(
            "Chọn file Excel (cần có cột CCCD hoặc Họ tên)",
            type=["xlsx", "xls"],
            key="ra_soat_upload"
        )
        
        if uploaded_file:
            try:
                df_input = pd.read_excel(uploaded_file)
                st.success(f"✅ Đã đọc {len(df_input)} dòng từ file")
                st.dataframe(df_input.head(10), use_container_width=True)
                
                # Xử lý rà soát
                if st.button("🔍 Bắt đầu rà soát", type="primary", key="btn_ra_soat_excel"):
                    with st.spinner("Đang rà soát..."):
                        results = process_batch_screening(df_input)
                        display_screening_results(results)
            except Exception as e:
                st.error(f"❌ Lỗi đọc file: {e}")
    
    with tab_paste:
        st.markdown("#### 📝 Nhập danh sách trực tiếp")
        st.caption("Mỗi dòng là một CCCD hoặc Họ tên")
        
        input_text = st.text_area(
            "Danh sách",
            placeholder="001234567890\nNguyễn Văn A\n002345678901\n...",
            height=200
        )
        
        if st.button("🔍 Bắt đầu rà soát", type="primary", key="btn_ra_soat_paste"):
            if input_text.strip():
                lines = [line.strip() for line in input_text.strip().split('\n') if line.strip()]
                df_input = pd.DataFrame({'input': lines})
                
                with st.spinner("Đang rà soát..."):
                    results = process_batch_screening(df_input)
                    display_screening_results(results)
            else:
                st.warning("⚠️ Vui lòng nhập danh sách!")

def process_batch_screening(df_input):
    """Xử lý rà soát với fuzzy matching"""
    from rapidfuzz import fuzz, process
    
    # Lấy danh sách đối tượng từ database
    conn = get_connection()
    df_db = pd.read_sql_query("SELECT cccd, ho_ten, ngay_sinh FROM doi_tuong", conn)
    conn.close()
    
    results = []
    
    # Xác định cột input
    if 'CCCD' in df_input.columns or 'cccd' in df_input.columns:
        col_name = 'CCCD' if 'CCCD' in df_input.columns else 'cccd'
        search_by = 'cccd'
    elif 'Họ tên' in df_input.columns or 'ho_ten' in df_input.columns:
        col_name = 'Họ tên' if 'Họ tên' in df_input.columns else 'ho_ten'
        search_by = 'ho_ten'
    elif 'input' in df_input.columns:
        col_name = 'input'
        search_by = 'auto'  # Tự động xác định
    else:
        col_name = df_input.columns[0]
        search_by = 'auto'
    
    for idx, row in df_input.iterrows():
        input_value = str(row[col_name]).strip()
        
        if not input_value:
            continue
        
        # Xác định loại search
        if search_by == 'auto':
            if input_value.isdigit() and len(input_value) == 12:
                current_search = 'cccd'
            else:
                current_search = 'ho_ten'
        else:
            current_search = search_by
        
        # Tìm kiếm
        if current_search == 'cccd':
            # Tìm chính xác CCCD
            match = df_db[df_db['cccd'] == input_value]
            if not match.empty:
                results.append({
                    'input': input_value,
                    'matched': match.iloc[0]['ho_ten'],
                    'cccd': match.iloc[0]['cccd'],
                    'status': '✅ Khớp chính xác',
                    'score': 100
                })
            else:
                results.append({
                    'input': input_value,
                    'matched': '',
                    'cccd': '',
                    'status': '❌ Không tìm thấy',
                    'score': 0
                })
        else:
            # Fuzzy matching họ tên
            if not df_db.empty:
                match_result = process.extractOne(
                    input_value, 
                    df_db['ho_ten'].tolist(),
                    scorer=fuzz.token_set_ratio
                )
                
                if match_result and match_result[1] >= 80:
                    matched_idx = df_db[df_db['ho_ten'] == match_result[0]].index[0]
                    results.append({
                        'input': input_value,
                        'matched': match_result[0],
                        'cccd': df_db.loc[matched_idx, 'cccd'],
                        'status': '✅ Khớp chính xác' if match_result[1] >= 95 else '⚠️ Nghi vấn',
                        'score': match_result[1]
                    })
                else:
                    results.append({
                        'input': input_value,
                        'matched': match_result[0] if match_result else '',
                        'cccd': '',
                        'status': '❌ Không tìm thấy',
                        'score': match_result[1] if match_result else 0
                    })
            else:
                results.append({
                    'input': input_value,
                    'matched': '',
                    'cccd': '',
                    'status': '❌ Database trống',
                    'score': 0
                })
    
    return results

def display_screening_results(results):
    """Hiển thị kết quả rà soát"""
    if not results:
        st.warning("Không có kết quả")
        return
    
    df_results = pd.DataFrame(results)
    
    # Thống kê
    st.markdown("---")
    st.markdown("### 📊 Kết quả rà soát")
    
    col1, col2, col3 = st.columns(3)
    
    exact_match = len([r for r in results if '✅' in r['status']])
    suspicious = len([r for r in results if '⚠️' in r['status']])
    not_found = len([r for r in results if '❌' in r['status']])
    
    col1.metric("✅ Khớp chính xác", exact_match)
    col2.metric("⚠️ Nghi vấn", suspicious)
    col3.metric("❌ Không tìm thấy", not_found)
    
    st.markdown("---")
    
    # Bảng kết quả
    df_display = df_results.rename(columns={
        'input': 'Đầu vào',
        'matched': 'Kết quả khớp',
        'cccd': 'CCCD',
        'status': 'Trạng thái',
        'score': 'Độ tương đồng (%)'
    })
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # Export
    st.download_button(
        label="📥 Xuất kết quả Excel",
        data=df_display.to_csv(index=False).encode('utf-8-sig'),
        file_name=f"ket_qua_ra_soat_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )

# ============================================
# ĐIỀU HƯỚNG CHÍNH
# ============================================
# Kiểm tra nếu đang xem profile
if st.session_state.view_profile_cccd:
    page_profile_view(st.session_state.view_profile_cccd)
elif menu == "🏠 Dashboard":
    page_dashboard()
elif menu == "📝 Nhập liệu":
    page_nhap_lieu()
elif menu == "📥 Nhập Excel":
    page_nhap_excel()
elif menu == "🔍 Tra cứu":
    page_tra_cuu()
elif menu == "🔎 Rà soát":
    page_ra_soat()
