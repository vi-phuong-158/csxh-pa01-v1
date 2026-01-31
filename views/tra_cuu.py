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
    2. Subsequence (các ký tự của query xuất hiện thứ tự trong text) - VIPHUONG -> Vi Ngoc Phuong
    """
    if not query or not text:
        return False

    n_query = normalize_string(query)
    n_text = normalize_string(text)

    # 1. Exact contains (relaxed)
    if n_query in n_text:
        return True

    # 2. Subsequence match (cho trường hợp viết tắt hoặc bỏ qua tên đệm)
    #    Ví dụ: "viphuong" -> "Vi Ngoc Phuong"
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
        st.button("🔍 Tìm kiếm", type="primary", use_container_width=True)

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
            st.selectbox(
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
            # Optimized by Bolt: Column Pruning + Two-step Fetch
            # 1. Fetch only necessary columns for filtering
            # 2. Perform fuzzy match in Python
            # 3. Fetch full details only for matching records

            # Fetch lightweight data
            sql_light = "SELECT cccd, ho_ten FROM doi_tuong WHERE 1=1"
            params = []

            if filter_tinh != "Tất cả":
                sql_light += " AND dia_chi_tinh = ?"
                params.append(filter_tinh)

            if filter_gioi_tinh != "Tất cả":
                sql_light += " AND gioi_tinh = ?"
                params.append(filter_gioi_tinh)

            df_light = pd.read_sql_query(sql_light, conn, params=params)

            # Pre-compute normalization
            query_norm = normalize_string(search_query)
            query_lower = search_query.lower()

            # 1. CCCD Match (Vectorized)
            mask_cccd = pd.Series(False, index=df_light.index)
            if search_type in ["Tất cả", "CCCD"]:
                mask_cccd = df_light['cccd'].astype(str).str.contains(
                    query_lower, case=False, na=False)

            # 2. Ho ten Match (Vectorized + Subsequence)
            mask_hoten = pd.Series(False, index=df_light.index)
            if search_type in ["Tất cả", "Họ tên"]:
                # Normalize 'ho_ten' column
                normalized_hoten = df_light['ho_ten'].apply(
                    lambda x: normalize_string(x) if x else "")

                # Check containment (Fast)
                mask_hoten_contains = normalized_hoten.str.contains(
                    query_norm, na=False, regex=False)
                mask_hoten = mask_hoten_contains

                # Check subsequence (Slower, only if query >= 3 chars)
                if len(query_norm) >= 3:
                    def check_subsequence(text_norm):
                        it = iter(text_norm)
                        return all(char in it for char in query_norm)

                    # Only check rows that failed containment
                    remaining_indices = ~mask_hoten_contains
                    if remaining_indices.any():
                        # We apply only to the remaining part
                        subsequence_matches = normalized_hoten[remaining_indices].apply(
                            check_subsequence)
                        # Update mask (using index alignment)
                        mask_hoten = mask_hoten | subsequence_matches.reindex(
                            df_light.index, fill_value=False
                        )

            # Combine masks
            final_mask = mask_cccd | mask_hoten

            # Extract matching CCCDs
            matching_cccds = df_light.loc[final_mask, 'cccd'].tolist()
            total_count = len(matching_cccds)

            st.info(
                f"🔍 Tìm thấy **{total_count}** kết quả cho: '{search_query}'")

            if matching_cccds:
                # 3. Fetch full details for matches
                # If too many matches, this query might be large, but still better than SELECT * ALL
                placeholders = ','.join(['?'] * len(matching_cccds))
                sql_full = (
                    f"SELECT cccd, ho_ten, ngay_sinh, gioi_tinh, dia_chi_xa, "
                    f"phan_loai_nghe_nghiep, dia_chi_tinh, "
                    f"chi_tiet_nghe_nghiep, ghi_chu_chung, created_at "
                    f"FROM doi_tuong WHERE cccd IN ({placeholders})"
                )
                df = pd.read_sql_query(sql_full, conn, params=matching_cccds)
            else:
                df = pd.DataFrame()

        else:
            # Optimized by Bolt: Push filters to SQL before pagination
            sql_where = " WHERE 1=1"
            params = []

            if filter_tinh != "Tất cả":
                sql_where += " AND dia_chi_tinh = ?"
                params.append(filter_tinh)

            if filter_gioi_tinh != "Tất cả":
                sql_where += " AND gioi_tinh = ?"
                params.append(filter_gioi_tinh)

            # Đếm tổng số records (filtered)
            count_query = f"SELECT COUNT(*) as total FROM doi_tuong{sql_where}"
            total_count = pd.read_sql_query(
                count_query, conn, params=params
            ).iloc[0, 0]

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
                    key="search_page"
                )

            offset = (current_page - 1) * ITEMS_PER_PAGE

            # Hiển thị với pagination (filtered)
            query = (
                f"SELECT cccd, ho_ten, ngay_sinh, gioi_tinh, dia_chi_xa, "
                f"phan_loai_nghe_nghiep, dia_chi_tinh, "
                f"chi_tiet_nghe_nghiep, ghi_chu_chung, created_at "
                f"FROM doi_tuong {sql_where} "
                f"ORDER BY created_at DESC "
                f"LIMIT {ITEMS_PER_PAGE} OFFSET {offset}"
            )
            df = pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()

    # Áp dụng bộ lọc (filters) - Đã thực hiện ở SQL, không cần filter lại
    # Tuy nhiên vẫn giữ logic pass cho bộ lọc đặc thù nếu có (hiện tại chưa có logic cho đặc thù trong code gốc)
    if not df.empty:
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
                columns={k: v for k, v in col_map.items()
                         if k in display_df.columns}
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
            options = [f"{row[cccd_col]} - {row[hoten_col]}" for _,
                       row in df.iterrows()]
            selected = st.selectbox(
                "Chọn đối tượng", options, key="select_profile")

        with col_btn:
            if st.button(
                "👁️ Xem hồ sơ",
                type="primary",
                use_container_width=True,
                help="Nhấn để xem chi tiết toàn bộ thông tin của đối tượng"
            ):
                if selected:
                    selected_cccd = selected.split(" - ")[0]
                    st.session_state.view_profile_cccd = selected_cccd
                    st.rerun()

        st.markdown("---")

        # Nút xuất Excel
        st.download_button(
            label="📥 Xuất Excel",
            data=sanitize_dataframe_for_csv(df).to_csv(
                index=False).encode('utf-8-sig'),
            file_name=f"danh_sach_doi_tuong_{datetime.now().strftime('%Y%m%d')}.csv",
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
