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
        # Variable assigned but unused: search_clicked
        # Kept for UI button rendering
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
            # Unused filter
            _ = st.selectbox(
                "Yếu tố đặc thù",
                ["Tất cả"] + list(LOAI_HINH_DAC_THU.values()),
                help="Lọc theo các loại hồ sơ chính sách xã hội "
                     "(kết hôn nước ngoài, xuất cảnh, v.v.)"
            )

    st.markdown("---")

    # Pagination settings
    ITEMS_PER_PAGE = 50
    # Add a unique key for pagination to reset when query changes
    pagination_key = f"search_page_{hash(search_query)}"

    # Thực hiện tìm kiếm
    st.markdown("### 📋 Kết quả")

    conn = get_connection()
    try:
        df_display = pd.DataFrame()
        # Will be populated only if needed or kept as partial
        df_export = pd.DataFrame()

        if search_query:
            # OPTIMIZATION (Bolt): Fetch only necessary columns for search
            # Instead of SELECT *, we select only columns needed for filtering
            # This reduces data transfer and memory usage significantly
            sql = "SELECT cccd, ho_ten FROM doi_tuong WHERE 1=1"
            params = []

            # Predicate Pushdown (Filters)
            if filter_tinh != "Tất cả":
                sql += " AND dia_chi_tinh = ?"
                params.append(filter_tinh)

            if filter_gioi_tinh != "Tất cả":
                sql += " AND gioi_tinh = ?"
                params.append(filter_gioi_tinh)

            # 1. Light Fetch
            df_light = pd.read_sql_query(sql, conn, params=params)

            # Pre-compute normalization
            query_norm = normalize_string(search_query)
            query_lower = search_query.lower()

            # 2. CCCD Match (Vectorized)
            mask_cccd = pd.Series(False, index=df_light.index)
            if search_type in ["Tất cả", "CCCD"]:
                mask_cccd = df_light['cccd'].astype(str).str.contains(
                    query_lower, case=False, na=False)

            # 3. Ho ten Match (Vectorized + Subsequence)
            mask_hoten = pd.Series(False, index=df_light.index)
            if search_type in ["Tất cả", "Họ tên"]:
                normalized_hoten = df_light['ho_ten'].apply(
                    lambda x: normalize_string(x) if x else "")

                mask_hoten_contains = normalized_hoten.str.contains(
                    query_norm, na=False, regex=False)
                mask_hoten = mask_hoten_contains

                if len(query_norm) >= 3:
                    def check_subsequence(text_norm):
                        it = iter(text_norm)
                        return all(char in it for char in query_norm)

                    remaining_indices = ~mask_hoten_contains
                    if remaining_indices.any():
                        subsequence_matches = normalized_hoten[
                            remaining_indices].apply(check_subsequence)
                        mask_hoten = mask_hoten | subsequence_matches.reindex(
                            df_light.index, fill_value=False)

            # Combine masks
            final_mask = mask_cccd | mask_hoten

            # Get list of matching CCCDs
            matching_cccds = df_light.loc[final_mask, 'cccd'].tolist()
            total_count = len(matching_cccds)

            st.info(f"🔍 Tìm thấy **{total_count}** kết quả "
                    f"cho: '{search_query}'")

            if total_count > 0:
                # Pagination for Search Results
                total_pages = max(
                    1, (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

                col_page1, col_page2, col_page3 = st.columns([1, 2, 1])
                with col_page2:
                    current_page = st.number_input(
                        f"Trang (tổng {total_pages} trang)",
                        min_value=1,
                        max_value=total_pages,
                        value=1,
                        key=pagination_key
                    )

                start_idx = (current_page - 1) * ITEMS_PER_PAGE
                end_idx = start_idx + ITEMS_PER_PAGE
                page_cccds = matching_cccds[start_idx:end_idx]

                # 4. Fetch Full Details for Displayed Page
                if page_cccds:
                    placeholders = ','.join(['?'] * len(page_cccds))
                    # Note: We don't filter by province/gender here because
                    # they were already filtered in Step 1
                    sql_details = f"""
                        SELECT cccd, ho_ten, ngay_sinh, gioi_tinh, dia_chi_xa,
                               phan_loai_nghe_nghiep, dia_chi_tinh,
                               chi_tiet_nghe_nghiep, ghi_chu_chung, created_at
                        FROM doi_tuong
                        WHERE cccd IN ({placeholders})
                    """
                    df_display = pd.read_sql_query(
                        sql_details, conn, params=page_cccds)

                # 5. Prepare Export Data (Fetch all matches if needed for export)
                # User expects to download ALL matches.
                # If total matches < 2000, we fetch all.
                if total_count <= 2000:
                    placeholders_all = ','.join(['?'] * len(matching_cccds))
                    sql_export = f"""
                        SELECT * FROM doi_tuong
                        WHERE cccd IN ({placeholders_all})
                    """
                    df_export = pd.read_sql_query(
                        sql_export, conn, params=matching_cccds)
                else:
                    # Fallback for huge results: Only export current page
                    df_export = df_display  # Limited export
                    st.warning("⚠️ Số lượng kết quả quá lớn (>2000). "
                               "File xuất sẽ chỉ chứa trang hiện tại.")

        else:
            # Default View (No Search Query)
            count_query = "SELECT COUNT(*) as total FROM doi_tuong"
            total_count = pd.read_sql_query(count_query, conn).iloc[0, 0]

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

            query = f"""
                SELECT cccd, ho_ten, ngay_sinh, gioi_tinh, dia_chi_xa,
                       phan_loai_nghe_nghiep, dia_chi_tinh,
                       chi_tiet_nghe_nghiep, ghi_chu_chung, created_at
                FROM doi_tuong
                ORDER BY created_at DESC
                LIMIT {ITEMS_PER_PAGE} OFFSET {offset}
            """
            df_display = pd.read_sql_query(query, conn)

            if not df_display.empty:
                if filter_tinh != "Tất cả":
                    df_display = df_display[
                        df_display['dia_chi_tinh'] == filter_tinh]
                if filter_gioi_tinh != "Tất cả":
                    df_display = df_display[
                        df_display['gioi_tinh'] == filter_gioi_tinh]

            # For export in default view
            df_export = df_display

    finally:
        conn.close()

    if not df_display.empty:
        # Đổi tên cột
        display_cols = df_display.copy()
        if 'cccd' in display_cols.columns:
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
            display_cols = display_cols.rename(
                columns={k: v for k, v in col_map.items()
                         if k in display_cols.columns})

        st.dataframe(display_cols, use_container_width=True, hide_index=True)

        st.markdown("---")

        # Chọn và xem hồ sơ chi tiết
        st.markdown("##### 👤 Xem hồ sơ chi tiết")
        col_select, col_btn = st.columns([3, 1])

        with col_select:
            # Tạo danh sách options: CCCD - Họ tên
            cccd_col = 'cccd' if 'cccd' in df_display.columns else 'CCCD'
            hoten_col = 'ho_ten' if 'ho_ten' in df_display.columns else 'Họ tên'
            options = [f"{row[cccd_col]} - {row[hoten_col]}" for _,
                       row in df_display.iterrows()]
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
        if not df_export.empty:
            now_str = datetime.now().strftime('%Y%m%d')
            st.download_button(
                label="📥 Xuất Excel",
                data=sanitize_dataframe_for_csv(df_export).to_csv(
                    index=False).encode('utf-8-sig'),
                file_name=f"danh_sach_doi_tuong_{now_str}.csv",
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
