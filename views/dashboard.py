# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from database import get_connection
from constants import (
    LOAI_HINH_DAC_THU,
)

# ECharts (primary) - với fallback Plotly
try:
    from streamlit_echarts import st_echarts
    ECHARTS_AVAILABLE = True
except ImportError:
    ECHARTS_AVAILABLE = False

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
        cursor.execute(
            "SELECT gioi_tinh, COUNT(*) FROM doi_tuong GROUP BY gioi_tinh")
        gioi_tinh_stats = dict(cursor.fetchall())

        # Số theo phân loại nghề nghiệp
        cursor.execute(
            "SELECT phan_loai_nghe_nghiep, COUNT(*) FROM doi_tuong GROUP BY phan_loai_nghe_nghiep")
        nghe_nghiep_stats = dict(cursor.fetchall())

        # Số hồ sơ đặc thù theo loại hình
        cursor.execute(
            "SELECT loai_hinh, COUNT(*) FROM ho_so_dac_thu GROUP BY loai_hinh")
        dac_thu_stats = dict(cursor.fetchall())

        return {
            "total": total_doi_tuong,
            "gioi_tinh": gioi_tinh_stats,
            "nghe_nghiep": nghe_nghiep_stats,
            "dac_thu": dac_thu_stats,
        }
    finally:
        conn.close()


@st.cache_data(ttl=60)
def get_recent_records(limit=10):
    """Lấy các bản ghi gần đây"""
    conn = get_connection()
    try:
        query = """
            SELECT cccd, ho_ten, ngay_sinh, gioi_tinh, dia_chi_xa, phan_loai_nghe_nghiep
            FROM doi_tuong
            ORDER BY created_at DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(limit,))
        return df
    finally:
        conn.close()


@st.cache_data(ttl=300)
def get_xa_phuong_stats():
    """Lấy thống kê theo xã/phường"""
    conn = get_connection()
    try:
        query = """
            SELECT dia_chi_xa, COUNT(*) as so_luong 
            FROM doi_tuong 
            WHERE dia_chi_xa IS NOT NULL AND dia_chi_xa != ''
            GROUP BY dia_chi_xa 
            ORDER BY so_luong DESC 
            LIMIT 10
        """
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()

# ... (Previous code remains same, skipping to page_dashboard updates)

# ============================================
# DASHBOARD PAGE
# ============================================
def page_dashboard():
    """Trang Dashboard - Tổng quan hệ thống với ECharts tương tác"""

    st.markdown("# 🏠 Dashboard")
    st.markdown("### Tổng quan hệ thống quản lý hồ sơ an ninh")

    # Check ECharts availability
    if not ECHARTS_AVAILABLE:
        st.warning(
            "⚠️ Để có biểu đồ tương tác, hãy cài: `pip install streamlit-echarts`")
        st.info("Đang sử dụng Plotly fallback...")

    st.markdown("---")

    # Thống kê chính
    with st.spinner("Đang tải thống kê hệ thống..."):
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
        dac_thu_total = sum(stats["dac_thu"].values()
                            ) if stats["dac_thu"] else 0
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
            if ECHARTS_AVAILABLE:
                render_pie_echarts(stats["gioi_tinh"], "Giới tính")
            else:
                render_pie_plotly(stats["gioi_tinh"], "Giới tính")
        else:
            st.info("💡 Chưa có dữ liệu giới tính.")

    with col_right:
        st.markdown("### 📊 Phân loại nghề nghiệp")
        if stats["nghe_nghiep"] and sum(stats["nghe_nghiep"].values()) > 0:
            if ECHARTS_AVAILABLE:
                render_bar_echarts(stats["nghe_nghiep"], "Nghề nghiệp")
            else:
                render_bar_plotly(stats["nghe_nghiep"], "Nghề nghiệp")
        else:
            st.info("💡 Chưa có dữ liệu nghề nghiệp.")

    st.markdown("---")

    # Row 2: Hồ sơ đặc thù + Top xã/phường
    col_left2, col_right2 = st.columns(2)

    with col_left2:
        st.markdown("### 🌐 Hồ sơ đặc thù CSXH")
        if stats["dac_thu"] and sum(stats["dac_thu"].values()) > 0:
            # Convert keys to readable names
            readable_dac_thu = {
                LOAI_HINH_DAC_THU.get(k, k): v
                for k, v in stats["dac_thu"].items()
            }
            if ECHARTS_AVAILABLE:
                render_bar_echarts(
                    readable_dac_thu, "Hồ sơ đặc thù", horizontal=False)
            else:
                render_bar_plotly(readable_dac_thu, "Hồ sơ đặc thù")
        else:
            st.info("💡 Chưa có hồ sơ đặc thù nào.")

    with col_right2:
        st.markdown("### 🏘️ Top 10 xã/phường")
        # Load data with spinner
        with st.spinner("Đang tải dữ liệu địa bàn..."):
            df_xa = get_xa_phuong_stats()

        if not df_xa.empty:
            if ECHARTS_AVAILABLE:
                # Convert DataFrame to dict for vertical bar chart
                xa_data = dict(
                    zip(df_xa['dia_chi_xa'].tolist(), df_xa['so_luong'].tolist()))
                render_bar_echarts(xa_data, "Top xã/phường", horizontal=False)
            else:
                fig_xa = px.bar(df_xa, y='dia_chi_xa', x='so_luong', orientation='h',
                                color='so_luong', color_continuous_scale='Viridis')
                fig_xa.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    margin=dict(t=20, b=20, l=20, r=20),
                    showlegend=False, coloraxis_showscale=False
                )
                st.plotly_chart(fig_xa, use_container_width=True)
        else:
            st.info("💡 Chưa có dữ liệu phân bố theo xã/phường.")

    st.markdown("---")

    # Bản ghi gần đây
    st.markdown("### 📋 Hồ sơ được thêm gần đây")
    with st.spinner("Đang tải hồ sơ gần đây..."):
        recent_df = get_recent_records(10)
        
    if not recent_df.empty:
        # Đổi tên cột cho dễ đọc
        recent_df.columns = ["CCCD", "Họ tên", "Ngày sinh",
                             "Giới tính", "Xã/Phường", "Phân loại"]
        st.dataframe(recent_df, use_container_width=True, hide_index=True)
    else:
        st.info("💡 Chưa có hồ sơ nào. Bấm vào **📝 Nhập liệu** để thêm mới.")
