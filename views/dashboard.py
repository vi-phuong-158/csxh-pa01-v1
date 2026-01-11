# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from database import get_connection
from constants import (
    LOAI_HINH_DAC_THU,
)

# Optional dependencies
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# ============================================
# HELPER FUNCTIONS
# ============================================
@st.cache_data(ttl=300)
def get_statistics():
    """Lấy thống kê tổng quan (cached)"""
    conn = get_connection()
    try:
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
        
        return {
            "total": total_doi_tuong,
            "gioi_tinh": gioi_tinh_stats,
            "nghe_nghiep": nghe_nghiep_stats,
            "dac_thu": dac_thu_stats,
        }
    finally:
        conn.close()

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

# ============================================
# DASHBOARD PAGE
# ============================================
def page_dashboard():
    """Trang Dashboard - Tổng quan hệ thống"""
    if not PLOTLY_AVAILABLE:
        st.warning("⚠️ Cần cài đặt plotly: `pip install plotly`")
        return
    
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
