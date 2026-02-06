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


def search_doi_tuong(conn, search_query, search_type,
                     filter_tinh, filter_gioi_tinh):
    """
    Thực hiện tìm kiếm đối tượng với chiến lược Column Pruning:
    1. Lấy index (cccd, ho_ten)
    2. Lọc bằng Python (fuzzy match)
    3. Lấy dữ liệu chi tiết cho các CCCD khớp
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
        return pd.DataFrame()

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

    if not matching_cccds:
        return pd.DataFrame()

    # 3. Fetch Full Details (Chunked)
    chunk_size = 900  # SQLite limit safe
    chunks = [matching_cccds[i:i + chunk_size]
              for i in range(0, len(matching_cccds), chunk_size)]

    dfs = []
    for chunk in chunks:
        placeholders = ','.join(['?'] * len(chunk))
        sql_details = f"SELECT * FROM doi_tuong WHERE cccd IN ({placeholders})"
        # IMPORTANT: Preserve order if needed?
        # Current logic sorts by created_at DESC in pagination,
        # but for search it was implicit (likely insertion order or PK).
        # We can sort later if needed.
        dfs.append(pd.read_sql_query(sql_details, conn, params=chunk))

    return pd.concat(dfs, ignore_index=True)


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
            # Optimized by Bolt: Column Pruning Strategy
            df = search_doi_tuong(
                conn, search_query, search_type, filter_tinh, filter_gioi_tinh)

            total_count = len(df)
            st.info(
                f"🔍 Tìm thấy **{total_count}** kết quả cho: '{search_query}'")
        else:
            # Đếm tổng số records
            count_query = "SELECT COUNT(*) as total FROM doi_tuong"
            total_count = pd.read_sql_query(count_query, conn).iloc[0, 0]

            # Pagination UI
            total_pages = max(
                1, (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

            # Pagination Controls
            col_page_prev, col_page_input, col_page_next = st.columns(
                [1, 2, 1])

            # Ensure key exists to avoid key error if accessed before widget
            if "search_page" not in st.session_state:
                st.session_state.search_page = 1

            with col_page_prev:
                if st.button("⬅️ Trước",
                             disabled=(st.session_state.search_page <= 1),
                             use_container_width=True,
                             help="Trang trước"):
                    st.session_state.search_page -= 1
                    st.rerun()

            with col_page_input:
                current_page = st.number_input(
                    f"Trang (tổng {total_pages})",
                    min_value=1,
                    max_value=total_pages,
                    key="search_page",
                    label_visibility="collapsed",
                    help=f"Nhập số trang (Tổng {total_pages} trang)"
                )
                # Helper text
                st.markdown(
                    f"<div style='text-align: center; color: gray; "
                    f"font-size: 0.8em; margin-top: -10px;'>"
                    f"Trang {current_page} / {total_pages} "
                    f"(Tổng {total_count} hồ sơ)</div>",
                    unsafe_allow_html=True
                )

            with col_page_next:
                if st.button("Sau ➡️",
                             disabled=(
                                 st.session_state.search_page >= total_pages),
                             use_container_width=True,
                             help="Trang sau"):
                    st.session_state.search_page += 1
                    st.rerun()

            offset = (current_page - 1) * ITEMS_PER_PAGE

            # Hiển thị với pagination
            query = f"""
                SELECT cccd, ho_ten, ngay_sinh, gioi_tinh, dia_chi_xa,
                       phan_loai_nghe_nghiep, dia_chi_tinh,
                       chi_tiet_nghe_nghiep, ghi_chu_chung, created_at
                FROM doi_tuong
                ORDER BY created_at DESC
                LIMIT {ITEMS_PER_PAGE} OFFSET {offset}
            """
            df = pd.read_sql_query(query, conn)
    finally:
        conn.close()

    # Áp dụng bộ lọc (filters) - Thực hiện trên DataFrame cho đơn giản
    # Note: search_doi_tuong applies filters, but reapplying is safe
    if not df.empty:
        if filter_tinh != "Tất cả":
            df = df[df['dia_chi_tinh'] == filter_tinh]
        if filter_gioi_tinh != "Tất cả":
            df = df[df['gioi_tinh'] == filter_gioi_tinh]

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
            # Use original df to get CCCD safely
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
