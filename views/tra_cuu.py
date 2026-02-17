# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_connection
from constants import (
    TINH_OPTIONS, GIOI_TINH_OPTIONS, LOAI_HINH_DAC_THU
)
from utils.text_utils import normalize_string
from utils.security_utils import sanitize_dataframe_for_csv


def is_fuzzy_match(query, text):
    """
    Kiểm tra query có phải là match của text không.
    Hỗ trợ:
    1. Containment (sau khi chuẩn hóa)
    2. Subsequence (các ký tự của query xuất hiện thứ tự trong text)
       - VIPHUONG -> Vi Ngoc Phuong
    """
    if not query or not text:
        return False

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


def get_search_candidates(conn, search_query, search_type,
                          filter_tinh, filter_gioi_tinh):
    """
    Thực hiện tìm kiếm đối tượng và trả về danh sách CCCD phù hợp.
    Chiến lược Column Pruning:
    1. Lấy index (cccd, ho_ten)
    2. Lọc bằng Python (fuzzy match)
    3. Trả về danh sách CCCD
    """
    # 1. Fetch lightweight index
    sql_index = "SELECT cccd, ho_ten FROM doi_tuong WHERE 1=1"
    params = []

    # Apply filters to SQL index query to reduce initial load
    if filter_tinh != "Tất cả":
        sql_index += " AND dia_chi_tinh = ?"
        params.append(filter_tinh)

    if filter_gioi_tinh != "Tất cả":
        sql_index += " AND gioi_tinh = ?"
        params.append(filter_gioi_tinh)

    df_index = pd.read_sql_query(sql_index, conn, params=params)

    if df_index.empty:
        return []

    # Pre-compute normalization
    query_norm = normalize_string(search_query)
    query_lower = search_query.lower()

    # 2. Apply Text Filters (Vectorized + Subsequence)

    # 2.1 CCCD Match (Vectorized)
    mask_cccd = pd.Series(False, index=df_index.index)
    if search_type in ["Tất cả", "CCCD"]:
        mask_cccd = df_index['cccd'].astype(str).str.contains(
            query_lower, case=False, na=False)

    # 2.2 Ho ten Match (Vectorized + Subsequence)
    mask_hoten = pd.Series(False, index=df_index.index)
    if search_type in ["Tất cả", "Họ tên"]:
        # Normalize 'ho_ten' column
        normalized_hoten = df_index['ho_ten'].apply(
            lambda x: normalize_string(x) if x else "")

        # Check containment (Fast)
        mask_hoten_contains = normalized_hoten.str.contains(
            query_norm,
            na=False,
            regex=False
        )
        mask_hoten = mask_hoten_contains

        # Check subsequence (Slower, only if query >= 3 chars)
        if len(query_norm) >= 3:
            def check_subsequence(text_norm):
                it = iter(text_norm)
                return all(char in it for char in query_norm)

            # Only check rows that failed containment
            remaining_indices = ~mask_hoten_contains
            if remaining_indices.any():
                subsequence_matches = normalized_hoten[
                    remaining_indices].apply(check_subsequence)
                mask_hoten = mask_hoten | subsequence_matches.reindex(
                    df_index.index, fill_value=False)

    # Combine masks
    final_mask = mask_cccd | mask_hoten
    matching_cccds = df_index[final_mask]['cccd'].tolist()

    return matching_cccds


def fetch_doi_tuong_details(conn, cccd_list):
    """Lấy thông tin chi tiết cho danh sách CCCD"""
    if not cccd_list:
        return pd.DataFrame()
        
    placeholders = ','.join(['?'] * len(cccd_list))
    sql_details = f"SELECT * FROM doi_tuong WHERE cccd IN ({placeholders})"
    
    # We want to preserve order of cccd_list if possible, but IN clause doesn't guarantee order.
    # However, for display purposes, we might want to sort by created_at DESC or relevance.
    # Let's sort by created_at DESC to match default view.
    sql_details += " ORDER BY created_at DESC"
    
    return pd.read_sql_query(sql_details, conn, params=cccd_list)


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
            placeholder="Nhập CCCD, họ tên (có thể viết tắt, vd: viphuong)...",
            label_visibility="collapsed",
            help="Hỗ trợ tìm kiếm theo CCCD hoặc Họ tên "
                 "(bao gồm tìm kiếm không dấu và viết tắt)"
        )

    with col2:
        search_type = st.selectbox(
            "Loại",
            ["Tất cả", "CCCD", "Họ tên"],
            label_visibility="collapsed"
        )

    with col3:
        # Assign to _ to avoid flake8 F841
        _ = st.button(
            "🔍 Tìm kiếm", type="primary", use_container_width=True)

    st.markdown("---")

    # Bộ lọc nâng cao
    with st.expander("🎛️ Bộ lọc nâng cao", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            filter_tinh = st.selectbox(
                "Tỉnh/TP",
                ["Tất cả"] + TINH_OPTIONS,
                help="Lọc danh sách theo Tỉnh/Thành phố thường trú"
            )
        with col2:
            filter_gioi_tinh = st.selectbox(
                "Giới tính",
                ["Tất cả"] + GIOI_TINH_OPTIONS,
                help="Lọc danh sách theo Giới tính"
            )
        with col3:
            # Assign to _ to avoid flake8 F841
            _ = st.selectbox(
                "Yếu tố đặc thù",
                ["Tất cả"] + list(LOAI_HINH_DAC_THU.values()),
                help="Lọc theo các loại hồ sơ chính sách xã hội "
                     "(kết hôn nước ngoài, xuất cảnh, v.v.)"
            )

    st.markdown("---")

    # Pagination settings
    ITEMS_PER_PAGE = 50

    # Thực hiện tìm kiếm
    st.markdown("### 📋 Kết quả")

    conn = get_connection()
    try:
        if search_query:
            # SEARCH MODE with Pagination
            # 1. Get candidates (List of CCCDs)
            candidates = get_search_candidates(
                conn, search_query, search_type, filter_tinh, filter_gioi_tinh)
            
            total_count = len(candidates)
            st.info(
                f"🔍 Tìm thấy **{total_count}** kết quả cho: '{search_query}'")
            
            if total_count > 0:
                # 2. Pagination UI
                total_pages = max(
                    1, (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

                col_page1, col_page2, col_page3 = st.columns([1, 2, 1])
                with col_page2:
                    current_page = st.number_input(
                        f"Trang (tổng {total_pages} trang, {total_count} hồ sơ)",
                        min_value=1,
                        max_value=total_pages,
                        value=1,
                        key="search_page_query"
                    )
                
                # 3. Slice candidates for current page
                offset = (current_page - 1) * ITEMS_PER_PAGE
                page_cccds = candidates[offset : offset + ITEMS_PER_PAGE]
                
                # 4. Fetch details for current page
                df = fetch_doi_tuong_details(conn, page_cccds)
            else:
                df = pd.DataFrame()

        else:
            # NO SEARCH MODE (Default View)
            # Đếm tổng số records với filter
            count_query = "SELECT COUNT(*) as total FROM doi_tuong WHERE 1=1"
            count_params = []
            
            if filter_tinh != "Tất cả":
                count_query += " AND dia_chi_tinh = ?"
                count_params.append(filter_tinh)
            
            if filter_gioi_tinh != "Tất cả":
                count_query += " AND gioi_tinh = ?"
                count_params.append(filter_gioi_tinh)

            total_count = pd.read_sql_query(count_query, conn, params=count_params).iloc[0, 0]

            # Pagination UI
            total_pages = max(
                1, (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

            col_page1, col_page2, col_page3 = st.columns([1, 2, 1])
            with col_page2:
                current_page = st.number_input(
                    f"Trang (tổng {total_pages} trang, {total_count} hồ sơ)",
                    min_value=1,
                    max_value=total_pages,
                    value=1,
                    key="search_page_default"
                )

            offset = (current_page - 1) * ITEMS_PER_PAGE

            # Hiển thị với pagination và filter SQL
            query = """
                SELECT cccd, ho_ten, ngay_sinh, gioi_tinh, dia_chi_xa,
                       phan_loai_nghe_nghiep, dia_chi_tinh,
                       chi_tiet_nghe_nghiep, ghi_chu_chung, created_at
                FROM doi_tuong
                WHERE 1=1
            """
            params = []
            
            if filter_tinh != "Tất cả":
                query += " AND dia_chi_tinh = ?"
                params.append(filter_tinh)
            
            if filter_gioi_tinh != "Tất cả":
                query += " AND gioi_tinh = ?"
                params.append(filter_gioi_tinh)
                
            query += """
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            params.extend([ITEMS_PER_PAGE, offset])
            
            df = pd.read_sql_query(query, conn, params=params)
    finally:
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
            display_df = display_df.rename(
                columns={k: v for k, v in col_map.items()
                         if k in display_df.columns})

        st.caption("💡 Chọn một dòng trong bảng để xem chi tiết hồ sơ.")
        event = st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            selection_mode="single-row",
            on_select="rerun",
            key="search_result_table"
        )

        if event.selection.rows:
            selected_index = event.selection.rows[0]
            # Use original df to get CCCD safely (indices align with display_df)
            selected_cccd = str(df.iloc[selected_index]['cccd'])
            st.session_state.view_profile_cccd = selected_cccd
            st.rerun()

        st.markdown("---")

        # Nút xuất Excel
        st.download_button(
            label="📥 Xuất Excel",
            data=sanitize_dataframe_for_csv(df).to_csv(
                index=False).encode('utf-8-sig'),
            file_name=f"danh_sach_doi_tuong_"
            f"{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
    else:
        st.info("💡 Không có dữ liệu.")
        if search_query:
            if st.button(f"➕ Thêm mới hồ sơ: {search_query}",
                         type="secondary", use_container_width=True):
                # Determine if numeric (CCCD) or text (Name)
                if search_query.isdigit() and len(search_query) == 12:
                    st.session_state.nl_cccd = search_query
                    st.session_state.nl_ho_ten = ""
                else:
                    st.session_state.nl_cccd = ""
                    st.session_state.nl_ho_ten = search_query

                # Navigate to Nhap lieu
                st.session_state.main_menu = "Nhập liệu"
                st.rerun()
        else:
            st.info("Hãy thêm đối tượng mới trong phần **📝 Nhập liệu**.")
