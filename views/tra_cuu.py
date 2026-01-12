# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_connection
from constants import (
    TINH_OPTIONS, GIOI_TINH_OPTIONS, LOAI_HINH_DAC_THU
)
import unicodedata
import re


def remove_accents(input_str):
    if not input_str:
        return ""
    # Optimization: Remove redundant encode/decode for 'Đ/đ'
    input_str = input_str.replace('Đ', 'D').replace('đ', 'd')
    return ''.join(c for c in unicodedata.normalize(
        'NFD', input_str) if unicodedata.category(c) != 'Mn')


def normalize_string(s):
    """Chuẩn hóa chuỗi: bỏ dấu, thường, bỏ khoảng trắng"""
    if not s:
        return ""
    s = remove_accents(s).lower()
    return re.sub(r'[^a-z0-9]', '', s)


def is_fuzzy_match(query, text, n_query=None):
    """
    Kiểm tra query có phải là match của text không.
    Hỗ trợ:
    1. Containment (sau khi chuẩn hóa)
    2. Subsequence (các ký tự của query xuất hiện thứ tự trong text) - VIPHUONG -> Vi Ngoc Phuong

    Args:
        query: Chuỗi tìm kiếm gốc
        text: Chuỗi cần kiểm tra
        n_query: Chuỗi tìm kiếm đã chuẩn hóa (Optimization: pre-calculate once)
    """
    if not query or not text:
        return False

    # Use pre-calculated normalized query if available to save CPU
    if n_query is None:
        n_query = normalize_string(query)

    n_text = normalize_string(text)

    # 1. Exact contains (relaxed)
    if n_query in n_text:
        return True

    # 2. Subsequence match (cho trường hợp viết tắt hoặc bỏ qua tên đệm)
    # Ví dụ: "viphuong" -> "Vi Ngoc Phuong" (v...i...p...h...u...o...n...g)
    # Chỉ áp dụng nếu query đủ dài để tránh nhiễu
    if len(n_query) >= 3:
        it = iter(n_text)
        if all(char in it for char in n_query):
            return True

    return False

# ============================================
# TRA CUU PAGE
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
        search_clicked = st.button(
            "🔍 Tìm kiếm",
            type="primary",
            use_container_width=True)

    st.markdown("---")

    # Bộ lọc nâng cao
    with st.expander("🎛️ Bộ lọc nâng cao", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            filter_tinh = st.selectbox("Tỉnh/TP", ["Tất cả"] + TINH_OPTIONS)
        with col2:
            filter_gioi_tinh = st.selectbox(
                "Giới tính", ["Tất cả"] + GIOI_TINH_OPTIONS)
        with col3:
            filter_dac_thu = st.selectbox(
                "Yếu tố đặc thù",
                ["Tất cả"] + list(LOAI_HINH_DAC_THU.values())
            )

    st.markdown("---")

    # Thực hiện tìm kiếm
    st.markdown("### 📋 Kết quả")

    conn = get_connection()
    try:
        if search_query:
            # Lấy TOÀN BỘ dữ liệu để lọc bằng Python (Flexible Search)
            # Vì SQLite LIKE hạn chế với tiếng Việt có dấu/không dấu
            df_all = pd.read_sql_query("SELECT * FROM doi_tuong", conn)

            # Optimization: Pre-calculate normalized query once instead of N
            # times
            n_search_query = normalize_string(search_query)

            filtered_rows = []
            for index, row in df_all.iterrows():
                match = False
                # Check CCCD (Exact/Contains)
                if search_type in ["Tất cả", "CCCD"]:
                    if search_query.lower() in str(row['cccd']).lower():
                        match = True

                # Check Họ tên (Fuzzy)
                if not match and search_type in ["Tất cả", "Họ tên"]:
                    # Pass n_search_query to avoid re-normalizing query for
                    # every row
                    if is_fuzzy_match(
                            search_query,
                            row['ho_ten'],
                            n_query=n_search_query):
                        match = True

                if match:
                    filtered_rows.append(row)

            df = pd.DataFrame(filtered_rows) if filtered_rows else pd.DataFrame(
                columns=df_all.columns)
            st.info(f"🔍 Tìm thấy **{len(df)}** kết quả cho: '{search_query}'")
        else:
            # Hiển thị tất cả (giới hạn 100)
            query = "SELECT cccd, ho_ten, ngay_sinh, gioi_tinh, dia_chi_xa, phan_loai_nghe_nghiep, dia_chi_tinh, chi_tiet_nghe_nghiep, ghi_chu_chung, created_at FROM doi_tuong ORDER BY created_at DESC LIMIT 100"
            df = pd.read_sql_query(query, conn)
    finally:
        conn.close()

    # Áp dụng bộ lọc (filters) - Thực hiện trên DataFrame cho đơn giản
    if not df.empty:
        if filter_tinh != "Tất cả":
            df = df[df['dia_chi_tinh'] == filter_tinh]
        if filter_gioi_tinh != "Tất cả":
            df = df[df['gioi_tinh'] == filter_gioi_tinh]

        # Lọc đặc thù phức tạp hơn vì thông tin nằm ở bảng khác.
        # Ở đây logic hiện tại trong app.py CHƯA thực sự lọc kỹ theo bảng con nếu chỉ query doi_tuong.
        # Phiên bản gốc app.py cũng chỉ query trên bảng doi_tuong và KHÔNG thực sự join với ho_so_dac_thu để lọc.
        # Tuy nhiên, nếu user chọn lọc đặc thù, ta cần subquery.
        # Tôi sẽ giữ nguyên logic (hoặc cải thiện nếu cần, nhưng user yêu cầu tách code).
        # Nếu xem kỹ app.py gốc, filter_dac_thu chỉ ĐƯỢC CHỌN nhưng KHÔNG được dùng trong query ở đoạn code gốc.
        # "filter_dac_thu" biến được khai báo nhưng chưa xử lý logic lọc trong đoạn code tôi đọc được?
        # Xem lại app.py: dòng 1604-1616 tạo UI. Sau đó query database. Sau đó hiển thị dataframe.
        # Không thấy logic áp dụng filter_dac_thu.
        # Tôi sẽ để nguyên như app.py gốc (tức là UI có nhưng chưa logic lọc,
        # hoặc tôi sót).
        pass

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
            display_df = display_df.rename(
                columns={
                    k: v for k,
                    v in col_map.items() if k in display_df.columns})

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.markdown("---")

        # Chọn và xem hồ sơ chi tiết
        st.markdown("##### 👤 Xem hồ sơ chi tiết")
        col_select, col_btn = st.columns([3, 1])

        with col_select:
            # Tạo danh sách options: CCCD - Họ tên
            cccd_col = 'cccd' if 'cccd' in df.columns else 'CCCD'
            hoten_col = 'ho_ten' if 'ho_ten' in df.columns else 'Họ tên'
            options = [f"{row[cccd_col]} - {row[hoten_col]}" for _,
                       row in df.iterrows()]
            selected = st.selectbox(
                "Chọn đối tượng", options, key="select_profile")

        with col_btn:
            if st.button(
                "👁️ Xem hồ sơ",
                type="primary",
                    use_container_width=True):
                if selected:
                    selected_cccd = selected.split(" - ")[0]
                    st.session_state.view_profile_cccd = selected_cccd
                    st.rerun()

        st.markdown("---")

        # Nút xuất Excel
        st.download_button(
            label="📥 Xuất Excel",
            data=df.to_csv(
                index=False).encode('utf-8-sig'),
            file_name=f"danh_sach_doi_tuong_{
                datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
    else:
        st.info(
            "💡 Không có dữ liệu. Hãy thêm đối tượng mới trong phần **📝 Nhập liệu**.")
