# -*- coding: utf-8 -*-
"""
Tra cứu toàn diện - Multi-table Search
Tìm kiếm xuyên suốt: CCCD, Họ tên, SĐT, Tài khoản NH, Biển số xe, Nhân thân
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_connection
from constants import (
    TINH_OPTIONS, GIOI_TINH_OPTIONS, LOAI_HINH_DAC_THU
)
from utils.text_utils import normalize_string, format_date_vn
from utils.security_utils import sanitize_dataframe_for_csv
from utils.ui_components import render_address_fields


# ============================================
# SEARCH TYPE DEFINITIONS
# ============================================

SEARCH_TYPES = [
    "Tất cả",
    "CCCD",
    "Họ tên",
    "📱 SĐT/Liên hệ",
    "🏦 Tài khoản NH",
    "🚗 Biển số xe",
    "👤 Nhân thân",
]


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
    if len(n_query) >= 3:
        it = iter(n_text)
        if all(char in it for char in n_query):
            return True

    return False


# ============================================
# SATELLITE TABLE SEARCH (Multi-table)
# ============================================

def search_satellite_tables(conn, search_query, search_type):
    """
    Tìm kiếm trong các bảng vệ tinh (lien_he, tai_chinh, phuong_tien, nhan_than).
    
    Returns:
        dict: {cccd: [list of match source descriptions]}
        Ví dụ: {'001234567890': ['📱 SĐT: 0987654321', '🏦 TK: 19001234567']}
    """
    results = {}  # {cccd: [source_descriptions]}
    query_lower = search_query.strip().lower()
    query_like = f"%{search_query.strip()}%"

    # --- 1. Tìm trong bảng LIÊN HỆ (SĐT, Email, MXH) ---
    if search_type in ["Tất cả", "📱 SĐT/Liên hệ"]:
        try:
            df_lienhe = pd.read_sql_query(
                """SELECT cccd, loai_lien_he, gia_tri 
                   FROM lien_he 
                   WHERE gia_tri LIKE ? 
                   LIMIT 200""",
                conn, params=[query_like]
            )
            for _, row in df_lienhe.iterrows():
                cccd = row['cccd']
                loai = row['loai_lien_he'] or 'Liên hệ'
                gia_tri = row['gia_tri'] or ''
                source = f"📱 {loai}: {gia_tri}"
                results.setdefault(cccd, []).append(source)
        except Exception:
            pass

    # --- 2. Tìm trong bảng TÀI CHÍNH (Số tài khoản, Chủ TK) ---
    if search_type in ["Tất cả", "🏦 Tài khoản NH"]:
        try:
            df_taichinh = pd.read_sql_query(
                """SELECT cccd, ngan_hang, so_tai_khoan, chu_tai_khoan 
                   FROM tai_chinh 
                   WHERE so_tai_khoan LIKE ? OR chu_tai_khoan LIKE ?
                   LIMIT 200""",
                conn, params=[query_like, query_like]
            )
            for _, row in df_taichinh.iterrows():
                cccd = row['cccd']
                bank = row['ngan_hang'] or ''
                stk = row['so_tai_khoan'] or ''
                source = f"🏦 TK {bank}: {stk}"
                results.setdefault(cccd, []).append(source)
        except Exception:
            pass

    # --- 3. Tìm trong bảng PHƯƠNG TIỆN (Biển kiểm soát) ---
    if search_type in ["Tất cả", "🚗 Biển số xe"]:
        try:
            df_phuongtien = pd.read_sql_query(
                """SELECT cccd, loai_xe, bien_kiem_soat, ten_phuong_tien
                   FROM phuong_tien 
                   WHERE bien_kiem_soat LIKE ?
                   LIMIT 200""",
                conn, params=[query_like]
            )
            for _, row in df_phuongtien.iterrows():
                cccd = row['cccd']
                loai = row['loai_xe'] or ''
                bks = row['bien_kiem_soat'] or ''
                source = f"🚗 {loai}: {bks}"
                results.setdefault(cccd, []).append(source)
        except Exception:
            pass

    # --- 4. Tìm trong bảng NHÂN THÂN (Họ tên, CCCD nhân thân) ---
    if search_type in ["Tất cả", "👤 Nhân thân"]:
        try:
            df_nhanthan = pd.read_sql_query(
                """SELECT cccd, loai_quan_he, ho_ten, cccd_nhan_than
                   FROM nhan_than 
                   WHERE ho_ten LIKE ? OR cccd_nhan_than LIKE ?
                   LIMIT 200""",
                conn, params=[query_like, query_like]
            )
            for _, row in df_nhanthan.iterrows():
                cccd = row['cccd']
                quan_he = row['loai_quan_he'] or ''
                ten_nt = row['ho_ten'] or ''
                source = f"👤 {quan_he}: {ten_nt}"
                results.setdefault(cccd, []).append(source)
        except Exception:
            pass

    return results


# ============================================
# CORE SEARCH CANDIDATES (UPGRADED)
# ============================================

def get_search_candidates(conn, search_query, search_type,
                          filter_tinh, filter_xa, filter_gioi_tinh):
    """
    Thực hiện tìm kiếm đối tượng và trả về danh sách CCCD phù hợp.
    Nâng cấp: Tìm trong cả bảng vệ tinh (lien_he, tai_chinh, phuong_tien, nhan_than).
    
    Returns:
        tuple: (matching_cccds: list, satellite_sources: dict)
        - matching_cccds: danh sách CCCD tìm thấy (giữ thứ tự)
        - satellite_sources: {cccd: [source_descriptions]} từ bảng vệ tinh
    """
    # ========== PHẦN 1: Tìm trong bảng doi_tuong (Logic cũ) ==========
    doi_tuong_cccds = []
    
    if search_type in ["Tất cả", "CCCD", "Họ tên"]:
        sql_index = "SELECT cccd, ho_ten FROM doi_tuong WHERE 1=1"
        params = []

        if filter_tinh != "Tất cả":
            sql_index += " AND dia_chi_tinh = ?"
            params.append(filter_tinh)
        
        if filter_xa != "Tất cả":
            sql_index += " AND dia_chi_xa = ?"
            params.append(filter_xa)

        if filter_gioi_tinh != "Tất cả":
            sql_index += " AND gioi_tinh = ?"
            params.append(filter_gioi_tinh)

        df_index = pd.read_sql_query(sql_index, conn, params=params)

        if not df_index.empty:
            query_norm = normalize_string(search_query)
            query_lower = search_query.lower()

            # CCCD Match (Vectorized)
            mask_cccd = pd.Series(False, index=df_index.index)
            if search_type in ["Tất cả", "CCCD"]:
                mask_cccd = df_index['cccd'].astype(str).str.contains(
                    query_lower, case=False, na=False)

            # Ho ten Match (Vectorized + Subsequence)
            mask_hoten = pd.Series(False, index=df_index.index)
            if search_type in ["Tất cả", "Họ tên"]:
                normalized_hoten = df_index['ho_ten'].apply(
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
                            df_index.index, fill_value=False)

            final_mask = mask_cccd | mask_hoten
            doi_tuong_cccds = df_index[final_mask]['cccd'].tolist()

    # ========== PHẦN 2: Tìm trong bảng vệ tinh ==========
    satellite_sources = {}
    
    if search_type in ["Tất cả", "📱 SĐT/Liên hệ", "🏦 Tài khoản NH", 
                        "🚗 Biển số xe", "👤 Nhân thân"]:
        satellite_sources = search_satellite_tables(conn, search_query, search_type)

    # ========== PHẦN 3: Merge kết quả (giữ thứ tự, loại bỏ trùng) ==========
    # Áp dụng bộ lọc tỉnh/giới tính cho kết quả satellite
    satellite_cccds_filtered = list(satellite_sources.keys())
    
    if satellite_cccds_filtered and (filter_tinh != "Tất cả" or filter_xa != "Tất cả" or filter_gioi_tinh != "Tất cả"):
        # Lọc satellite CCCDs theo filter
        placeholders = ','.join(['?'] * len(satellite_cccds_filtered))
        filter_sql = f"SELECT cccd FROM doi_tuong WHERE cccd IN ({placeholders})"
        filter_params = list(satellite_cccds_filtered)
        
        if filter_tinh != "Tất cả":
            filter_sql += " AND dia_chi_tinh = ?"
            filter_params.append(filter_tinh)
        if filter_xa != "Tất cả":
            filter_sql += " AND dia_chi_xa = ?"
            filter_params.append(filter_xa)
        if filter_gioi_tinh != "Tất cả":
            filter_sql += " AND gioi_tinh = ?"
            filter_params.append(filter_gioi_tinh)
        
        try:
            df_filtered = pd.read_sql_query(filter_sql, conn, params=filter_params)
            valid_cccds = set(df_filtered['cccd'].tolist())
            satellite_cccds_filtered = [c for c in satellite_cccds_filtered if c in valid_cccds]
            # Cũng lọc sources dict
            satellite_sources = {k: v for k, v in satellite_sources.items() if k in valid_cccds}
        except Exception:
            pass

    # Merge: doi_tuong trước, satellite sau (loại trùng)
    seen = set(doi_tuong_cccds)
    merged = list(doi_tuong_cccds)
    for cccd in satellite_cccds_filtered:
        if cccd not in seen:
            merged.append(cccd)
            seen.add(cccd)

    return merged, satellite_sources


def fetch_doi_tuong_details(conn, cccd_list):
    """Lấy thông tin chi tiết cho danh sách CCCD"""
    if not cccd_list:
        return pd.DataFrame()
        
    placeholders = ','.join(['?'] * len(cccd_list))
    sql_details = f"SELECT * FROM doi_tuong WHERE cccd IN ({placeholders})"
    sql_details += " ORDER BY created_at DESC"
    
    return pd.read_sql_query(sql_details, conn, params=cccd_list)


# ============================================
# TRA CUU PAGE
# ============================================


def page_tra_cuu():
    """Trang Tra cứu - Tìm kiếm đối tượng toàn diện"""
    st.markdown("# 🔍 Tra cứu")
    st.markdown("### Tìm kiếm và tra cứu hồ sơ đối tượng")

    st.markdown("---")

    # Thanh tìm kiếm
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        search_query = st.text_input(
            "Tìm kiếm",
            placeholder="Nhập CCCD, họ tên, SĐT, số tài khoản, biển số xe, tên nhân thân...",
            label_visibility="collapsed"
        )

    with col2:
        search_type = st.selectbox(
            "Loại",
            SEARCH_TYPES,
            label_visibility="collapsed"
        )

    with col3:
        _ = st.button(
            "🔍 Tìm kiếm", type="primary", use_container_width=True)

    st.markdown("---")

    # Bộ lọc nâng cao
    with st.expander("🎛️ Bộ lọc nâng cao", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            filter_tinh, filter_xa, _ = render_address_fields(
                prefix="filter_search",
                default_tinh="Tất cả",
                default_xa="Tất cả",
                include_all=True
            )
        with col2:
            filter_gioi_tinh = st.selectbox(
                "Giới tính",
                ["Tất cả"] + GIOI_TINH_OPTIONS,
                key="filter_gioi_tinh_search"
            )
        with col3:
            _ = st.selectbox(
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
        if search_query:
            # SEARCH MODE with Multi-table Search
            candidates, satellite_sources = get_search_candidates(
                conn, search_query, search_type, filter_tinh, filter_xa, filter_gioi_tinh)
            
            total_count = len(candidates)
            
            # Hiển thị thông báo kết quả kèm nguồn
            satellite_count = len(satellite_sources)
            if satellite_count > 0:
                st.info(
                    f"🔍 Tìm thấy **{total_count}** kết quả cho: '{search_query}' "
                    f"(trong đó **{satellite_count}** từ dữ liệu vệ tinh: liên hệ, tài chính, phương tiện, nhân thân)")
            else:
                st.info(
                    f"🔍 Tìm thấy **{total_count}** kết quả cho: '{search_query}'")
            
            if total_count > 0:
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
                        key="search_page_query"
                    )
                
                # Slice candidates for current page
                offset = (current_page - 1) * ITEMS_PER_PAGE
                page_cccds = candidates[offset : offset + ITEMS_PER_PAGE]
                
                # Fetch details for current page
                df = fetch_doi_tuong_details(conn, page_cccds)
                
                # === THÊM CỘT NGUỒN TRA CỨU ===
                if not df.empty and satellite_sources:
                    df['nguon_tra_cuu'] = df['cccd'].apply(
                        lambda c: ' | '.join(satellite_sources.get(c, []))
                    )
            else:
                df = pd.DataFrame()

        else:
            # NO SEARCH MODE (Default View) - giữ nguyên logic cũ
            satellite_sources = {}
            count_query = "SELECT COUNT(*) as total FROM doi_tuong WHERE 1=1"
            count_params = []
            
            if filter_tinh != "Tất cả":
                count_query += " AND dia_chi_tinh = ?"
                count_params.append(filter_tinh)
            
            if filter_xa != "Tất cả":
                count_query += " AND dia_chi_xa = ?"
                count_params.append(filter_xa)
            
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

            query = """
                SELECT cccd, ho_ten, ngay_sinh, gioi_tinh, dia_chi_chi_tiet, dia_chi_xa,
                       phan_loai_nghe_nghiep, dia_chi_tinh,
                       chi_tiet_nghe_nghiep, ghi_chu_chung, created_at
                FROM doi_tuong
                WHERE 1=1
            """
            params = []
            
            if filter_tinh != "Tất cả":
                query += " AND dia_chi_tinh = ?"
                params.append(filter_tinh)
            
            if filter_xa != "Tất cả":
                query += " AND dia_chi_xa = ?"
                params.append(filter_xa)
            
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
        if 'ngay_sinh' in display_df.columns:
            display_df['ngay_sinh'] = display_df['ngay_sinh'].apply(format_date_vn)
            
        if 'cccd' in display_df.columns:
            col_map = {
                'cccd': 'CCCD',
                'ho_ten': 'Họ tên',
                'ngay_sinh': 'Ngày sinh',
                'gioi_tinh': 'Giới tính',
                'dia_chi_chi_tiet': 'Số nhà/Đường',
                'dia_chi_xa': 'Xã/Phường',
                'phan_loai_nghe_nghiep': 'Phân loại',
                'dia_chi_tinh': 'Tỉnh/TP',
                'chi_tiet_nghe_nghiep': 'Nơi làm việc',
                'ghi_chu_chung': 'Ghi chú',
                'nguon_tra_cuu': '🔗 Nguồn tra cứu',
            }
            display_df = display_df.rename(
                columns={k: v for k, v in col_map.items()
                         if k in display_df.columns})

        # Loại bỏ các cột không cần thiết cho hiển thị
        hide_cols = ['created_at', 'updated_at', 'anh_chan_dung']
        for col in hide_cols:
            if col in display_df.columns:
                display_df = display_df.drop(columns=[col])

        st.caption("💡 Chọn một dòng trong bảng để xem chi tiết hồ sơ.")
        
        # Highlight cột nguồn tra cứu nếu có
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
            selected_cccd = str(df.iloc[selected_index]['cccd'])
            st.session_state.view_profile_cccd = selected_cccd
            st.rerun()

        st.markdown("---")

        # Nút xuất Excel
        export_df = df.copy()
        if 'nguon_tra_cuu' not in export_df.columns:
            export_df['nguon_tra_cuu'] = ''
        
        st.download_button(
            label="📥 Xuất Excel",
            data=sanitize_dataframe_for_csv(export_df).to_csv(
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
                if search_query.isdigit() and len(search_query) == 12:
                    st.session_state.nl_cccd = search_query
                    st.session_state.nl_ho_ten = ""
                else:
                    st.session_state.nl_cccd = ""
                    st.session_state.nl_ho_ten = search_query

                st.session_state.main_menu = "Nhập liệu"
                st.rerun()
        else:
            st.info("Hãy thêm đối tượng mới trong phần **📝 Nhập liệu**.")
