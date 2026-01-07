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
)
from bulk_import import create_excel_template, validate_excel_data, bulk_import_all, export_error_excel

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
# SIDEBAR - ĐIỀU HƯỚNG
# ============================================
with st.sidebar:
    st.markdown("# 🛡️ Security Profile 360")
    st.markdown("---")
    
    # Menu điều hướng với text ngắn gọn
    menu = st.radio(
        "Điều hướng",
        options=["🏠 Dashboard", "📝 Nhập liệu", "📥 Nhập Excel", "🔍 Tra cứu"],
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
    
    # Biểu đồ phân loại
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("### 📊 Phân loại theo nghề nghiệp")
        if stats["nghe_nghiep"]:
            df_nghe = pd.DataFrame(
                list(stats["nghe_nghiep"].items()),
                columns=["Phân loại", "Số lượng"]
            )
            st.bar_chart(df_nghe.set_index("Phân loại"))
        else:
            st.info("💡 Chưa có dữ liệu. Hãy thêm đối tượng mới trong mục **Nhập liệu**.")
    
    with col_right:
        st.markdown("### 🌐 Phân loại hồ sơ đặc thù")
        if stats["dac_thu"]:
            df_dac_thu = pd.DataFrame(
                [(LOAI_HINH_DAC_THU.get(k, k), v) for k, v in stats["dac_thu"].items()],
                columns=["Loại hình", "Số lượng"]
            )
            st.bar_chart(df_dac_thu.set_index("Loại hình"))
        else:
            st.info("💡 Chưa có hồ sơ đặc thù nào.")
    
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
    tab1, tab2, tab3 = st.tabs([
        "👤 Thông tin cá nhân",
        "📞 Liên hệ & Tài sản",
        "🌐 Yếu tố nước ngoài"
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
        
        # ===== PHẦN NHÂN THÂN =====
        st.markdown("#### 👨‍👩‍👧‍👦 Thông tin nhân thân")
        
        # Khởi tạo session state cho quan hệ khác
        if 'nhan_than_khac_count' not in st.session_state:
            st.session_state.nhan_than_khac_count = 0
        
        # Tabs cho các loại quan hệ
        tab_bo, tab_me, tab_vo_chong, tab_khac = st.tabs([
            "👨 Bố đẻ", "👩 Mẹ đẻ", "💑 Vợ/Chồng", "👥 Quan hệ khác"
        ])
        
        # === BỐ ĐẺ ===
        with tab_bo:
            col_bo1, col_bo2 = st.columns(2)
            with col_bo1:
                bo_ho_ten = st.text_input("Họ và tên", placeholder="Nguyễn Văn A", key="bo_ho_ten")
                bo_cccd = st.text_input("Số CCCD", placeholder="Nhập 12 số CCCD", key="bo_cccd")
                bo_ngay_sinh = st.date_input("Ngày sinh", value=None, key="bo_ngay_sinh", format="DD/MM/YYYY")
            with col_bo2:
                bo_nghe_nghiep = st.text_input("Nghề nghiệp", placeholder="Ví dụ: Nông dân, Công nhân...", key="bo_nghe_nghiep")
                bo_noi_o = st.text_input("Nơi ở hiện nay", placeholder="Địa chỉ hiện tại", key="bo_noi_o")
        
        # === MẸ ĐẺ ===
        with tab_me:
            col_me1, col_me2 = st.columns(2)
            with col_me1:
                me_ho_ten = st.text_input("Họ và tên", placeholder="Nguyễn Thị B", key="me_ho_ten")
                me_cccd = st.text_input("Số CCCD", placeholder="Nhập 12 số CCCD", key="me_cccd")
                me_ngay_sinh = st.date_input("Ngày sinh", value=None, key="me_ngay_sinh", format="DD/MM/YYYY")
            with col_me2:
                me_nghe_nghiep = st.text_input("Nghề nghiệp", placeholder="Ví dụ: Nội trợ, Buôn bán...", key="me_nghe_nghiep")
                me_noi_o = st.text_input("Nơi ở hiện nay", placeholder="Địa chỉ hiện tại", key="me_noi_o")
        
        # === VỢ/CHỒNG ===
        with tab_vo_chong:
            col_vc1, col_vc2 = st.columns(2)
            with col_vc1:
                vc_ho_ten = st.text_input("Họ và tên", placeholder="Họ tên vợ/chồng", key="vc_ho_ten")
                vc_cccd = st.text_input("Số CCCD", placeholder="Nhập 12 số CCCD", key="vc_cccd")
                vc_ngay_sinh = st.date_input("Ngày sinh", value=None, key="vc_ngay_sinh", format="DD/MM/YYYY")
            with col_vc2:
                vc_nghe_nghiep = st.text_input("Nghề nghiệp", placeholder="Ví dụ: Giáo viên, Bác sĩ...", key="vc_nghe_nghiep")
                vc_noi_o = st.text_input("Nơi ở hiện nay", placeholder="Địa chỉ hiện tại", key="vc_noi_o")
        
        # === QUAN HỆ KHÁC ===
        with tab_khac:
            st.caption("Thêm các mối quan hệ đáng chú ý khác (anh em, họ hàng, bạn bè...)")
            
            # Nút thêm quan hệ mới
            col_add, col_remove = st.columns([1, 1])
            with col_add:
                if st.button("➕ Thêm quan hệ", key="add_relation"):
                    st.session_state.nhan_than_khac_count += 1
            with col_remove:
                if st.session_state.nhan_than_khac_count > 0:
                    if st.button("➖ Xóa quan hệ cuối", key="remove_relation"):
                        st.session_state.nhan_than_khac_count -= 1
            
            # Lưu thông tin quan hệ khác
            nhan_than_khac_list = []
            
            for i in range(st.session_state.nhan_than_khac_count):
                st.markdown(f"**Quan hệ {i+1}**")
                col_qh1, col_qh2 = st.columns(2)
                with col_qh1:
                    qh_loai = st.selectbox(
                        "Loại quan hệ",
                        ["Anh/Chị em ruột", "Anh/Chị em họ", "Ông/Bà", "Bạn thân", "Đồng nghiệp", "Khác"],
                        key=f"qh_loai_{i}"
                    )
                    qh_ho_ten = st.text_input("Họ và tên", key=f"qh_ho_ten_{i}")
                    qh_cccd = st.text_input("Số CCCD", key=f"qh_cccd_{i}")
                with col_qh2:
                    qh_ngay_sinh = st.date_input("Ngày sinh", value=None, key=f"qh_ngay_sinh_{i}", format="DD/MM/YYYY")
                    qh_nghe_nghiep = st.text_input("Nghề nghiệp", key=f"qh_nghe_nghiep_{i}")
                    qh_noi_o = st.text_input("Nơi ở hiện nay", key=f"qh_noi_o_{i}")
                
                nhan_than_khac_list.append({
                    'loai_quan_he': qh_loai,
                    'ho_ten': qh_ho_ten,
                    'cccd': qh_cccd,
                    'ngay_sinh': qh_ngay_sinh.strftime('%Y-%m-%d') if qh_ngay_sinh else None,
                    'nghe_nghiep': qh_nghe_nghiep,
                    'noi_o': qh_noi_o
                })
                st.markdown("---")
        
        st.markdown("---")
        
        # Nút lưu
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
        
        with col_btn1:
            if st.button("💾 Lưu hồ sơ", type="primary", use_container_width=True):
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
            
            if st.button("➕ Thêm liên hệ", use_container_width=True):
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
            
            ngan_hang = st.text_input("Ngân hàng", placeholder="Vietcombank, BIDV, Agribank...")
            so_tai_khoan = st.text_input("Số tài khoản", placeholder="1234567890")
            chu_tai_khoan = st.text_input("Chủ tài khoản", placeholder="NGUYEN VAN A")
            
            if st.button("➕ Thêm tài khoản", use_container_width=True):
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
        
        if st.button("➕ Thêm phương tiện", use_container_width=True):
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
                noi_dung_dict["quoc_tich"] = st.text_input("Quốc tịch", key="hn_qt")
            with col2:
                noi_dung_dict["so_ho_chieu"] = st.text_input("Số hộ chiếu", key="hn_hc")
                noi_dung_dict["tinh_trang"] = st.selectbox(
                    "Tình trạng", 
                    ["Đang chung sống", "Đã ly hôn", "Đã qua đời"],
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
                noi_dung_dict["quoc_gia"] = st.text_input("Quốc gia", key="ht_qg")
            with col2:
                noi_dung_dict["thoi_gian_di"] = st.text_input("Thời gian đi", key="ht_tgd")
                noi_dung_dict["thoi_gian_ve"] = st.text_input("Thời gian về", key="ht_tgv")
            noi_dung_dict["nghe_sau_ve"] = st.text_input("Nghề nghiệp sau khi về", key="ht_nghe")
                
        elif loai_hinh == "Vi_Pham_NN":
            st.markdown("##### ⚠️ Thông tin vi phạm pháp luật ở nước ngoài")
            col1, col2 = st.columns(2)
            with col1:
                noi_dung_dict["quoc_gia"] = st.text_input("Quốc gia", key="vp_qg")
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
# ĐIỀU HƯỚNG CHÍNH
# ============================================
if menu == "🏠 Dashboard":
    page_dashboard()
elif menu == "📝 Nhập liệu":
    page_nhap_lieu()
elif menu == "📥 Nhập Excel":
    page_nhap_excel()
elif menu == "🔍 Tra cứu":
    page_tra_cuu()
