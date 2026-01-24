# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_connection
from constants import (
    TINH_OPTIONS, GIOI_TINH_OPTIONS, LOAI_HINH_DAC_THU
)
from utils.text_utils import normalize_string


def is_fuzzy_match(query, text):
    """
    Kiểm tra query có phải là match của text không.
    Hỗ trợ:
    1. Containment (sau khi chuẩn hóa)
    2. Subsequence (các ký tự của query xuất hiện thứ tự trong text)
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
        # Search button assigned but not used in logic (Streamlit reactive)
        st.button("🔍 Tìm kiếm", type="primary", use_container_width=True)

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
            # unused variable filter_dac_thu
            st.selectbox(
                "Yếu tố đặc thù",
                ["Tất cả"] + list(LOAI_HINH_DAC_THU.values())
            )

    st.markdown("---")

    # Pagination settings
    ITEMS_PER_PAGE = 50

    # Thực hiện tìm kiếm
    st.markdown("### 📋 Kết quả")

    conn = get_connection()
    try:
        # ⚡ Bolt Optimization: Push filters to SQL
        # Construct SQL Filters
        where_clauses = ["1=1"]
        params = []

        if filter_tinh != "Tất cả":
            where_clauses.append("dia_chi_tinh = ?")
            params.append(filter_tinh)

        if filter_gioi_tinh != "Tất cả":
            where_clauses.append("gioi_tinh = ?")
            params.append(filter_gioi_tinh)

        if search_query:
            # Optimization: If searching by CCCD, do it in SQL
            if search_type == "CCCD":
                where_clauses.append("cccd LIKE ?")
                params.append(f"%{search_query}%")

            # Construct Base Query
            where_str = " AND ".join(where_clauses)
            query = f"SELECT * FROM doi_tuong WHERE {where_str}"

            # Load FILTERED data (significantly smaller than SELECT *)
            df_filtered = pd.read_sql_query(query, conn, params=params)

            # Python Fuzzy Search (only if needed)
            if search_type != "CCCD":
                query_norm = normalize_string(search_query)
                query_lower = search_query.lower()

                # 1. CCCD Match (Vectorized) - still useful if "Tất cả"
                mask_cccd = pd.Series(False, index=df_filtered.index)
                if search_type in ["Tất cả", "CCCD"]:
                    mask_cccd = df_filtered['cccd'].astype(str).str.contains(
                        query_lower, case=False, na=False
                    )

                # 2. Ho ten Match (Vectorized + Subsequence)
                mask_hoten = pd.Series(False, index=df_filtered.index)
                if search_type in ["Tất cả", "Họ tên"]:
                    normalized_hoten = df_filtered['ho_ten'].apply(
                        lambda x: normalize_string(x) if x else ""
                    )

                    mask_hoten_contains = normalized_hoten.str.contains(
                        query_norm, na=False, regex=False
                    )
                    mask_hoten = mask_hoten_contains

                    if len(query_norm) >= 3:
                        def check_subsequence(text_norm):
                            it = iter(text_norm)
                            return all(char in it for char in query_norm)

                        remaining_indices = ~mask_hoten_contains
                        if remaining_indices.any():
                            subsequence_matches = normalized_hoten[
                                remaining_indices
                            ].apply(check_subsequence)
                            mask_hoten = (
                                mask_hoten | subsequence_matches.reindex(
                                    df_filtered.index, fill_value=False
                                )
                            )

                final_mask = mask_cccd | mask_hoten
                df = df_filtered[final_mask]
            else:
                df = df_filtered

            total_count = len(df)
            st.info(
                f"🔍 Tìm thấy **{total_count}** kết quả cho: '{search_query}'"
            )
        else:
            # Browsing Mode (No Search Query)
            where_str = " AND ".join(where_clauses)

            # Count with filters
            count_query = (
                f"SELECT COUNT(*) as total FROM doi_tuong WHERE {where_str}"
            )
            total_count = pd.read_sql_query(
                count_query, conn, params=params
            ).iloc[0, 0]

            # Pagination UI
            total_pages = max(
                1, (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
            )

            col_page1, col_page2, col_page3 = st.columns([1, 2, 1])
            with col_page2:
                current_page = st.number_input(
                    f"Trang (tổng {total_pages} trang, {total_count} hồ sơ)",
                    min_value=1,
                    max_value=total_pages,
                    value=1,
                    key="search_page"
                )

            offset = (current_page - 1) * ITEMS_PER_PAGE

            # Data with filters and pagination
            query = f"""
                SELECT cccd, ho_ten, ngay_sinh, gioi_tinh, dia_chi_xa,
                       phan_loai_nghe_nghiep, dia_chi_tinh,
                       chi_tiet_nghe_nghiep, ghi_chu_chung, created_at
                FROM doi_tuong
                WHERE {where_str}
                ORDER BY created_at DESC
                LIMIT {ITEMS_PER_PAGE} OFFSET {offset}
            """
            df = pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()

    # ⚡ Bolt Note: Filters are now applied in SQL.
    # Lọc đặc thù phức tạp hơn vì thông tin nằm ở bảng khác.
    # Logic này chưa được implement trong phiên bản gốc.
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
                    k: v for k, v in col_map.items()
                    if k in display_df.columns
                }
            )

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.markdown("---")

        # Chọn và xem hồ sơ chi tiết
        st.markdown("##### 👤 Xem hồ sơ chi tiết")
        col_select, col_btn = st.columns([3, 1])

        with col_select:
            # Tạo danh sách options: CCCD - Họ tên
            cccd_col = 'cccd' if 'cccd' in df.columns else 'CCCD'
            hoten_col = 'ho_ten' if 'ho_ten' in df.columns else 'Họ tên'
            options = [
                f"{row[cccd_col]} - {row[hoten_col]}"
                for _, row in df.iterrows()
            ]
            selected = st.selectbox(
                "Chọn đối tượng", options, key="select_profile"
            )

        with col_btn:
            if st.button(
                "👁️ Xem hồ sơ", type="primary", use_container_width=True
            ):
                if selected:
                    selected_cccd = selected.split(" - ")[0]
                    st.session_state.view_profile_cccd = selected_cccd
                    st.rerun()

        st.markdown("---")

        # Nút xuất Excel
        st.download_button(
            label="📥 Xuất Excel",
            data=df.to_csv(index=False).encode('utf-8-sig'),
            file_name=(
                f"danh_sach_doi_tuong_"
                f"{datetime.now().strftime('%Y%m%d')}.csv"
            ),
            mime="text/csv",
        )
    else:
        st.info(
            "💡 Không có dữ liệu. Hãy thêm đối tượng mới trong phần "
            "**📝 Nhập liệu**."
        )
