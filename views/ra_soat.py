# -*- coding: utf-8 -*-
"""
Rà soát hàng loạt - Sử dụng Fuzzy Matching với ngưỡng 80%
Pattern từ thefuzz/rapidfuzz
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_connection

# Import fuzzy matching module
try:
    from utils.fuzzy_matching import (
        batch_screen,
        classify_match,
        compare_names,
        THRESHOLD_SUSPECT,
        THRESHOLD_EXACT
    )
    FUZZY_MODULE_AVAILABLE = True
except ImportError:
    FUZZY_MODULE_AVAILABLE = False

# Fallback to rapidfuzz directly
try:
    from rapidfuzz import process as fuzz_process
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False

from utils.security_utils import sanitize_dataframe_for_csv

# ============================================
# CORE SCREENING FUNCTIONS
# ============================================

@st.cache_data(ttl=300)
def get_database_names():
    """Lấy danh sách họ tên từ database (Cached 5 min)"""
    conn = get_connection()
    try:
        df = pd.read_sql_query(
            "SELECT cccd, ho_ten, ngay_sinh FROM doi_tuong", conn)
        return df
    finally:
        conn.close()


def process_batch_screening_v2(df_input):
    """
    Xử lý rà soát với fuzzy matching module mới.
    Sử dụng ngưỡng 80% đã được user phê duyệt.
    """
    if not FUZZY_MODULE_AVAILABLE and not RAPIDFUZZ_AVAILABLE:
        return [{
            "input": "Lỗi",
            "matched": "",
            "cccd": "",
            "status": "⚠️ Cần cài rapidfuzz: pip install rapidfuzz",
            "score": 0
        }]

    # Lấy danh sách đối tượng từ database
    df_db = get_database_names()

    if df_db.empty:
        return [{
            "input": "Lỗi",
            "matched": "",
            "cccd": "",
            "status": "❌ Database trống",
            "score": 0
        }]

    results = []

    # Xác định cột input
    if 'CCCD' in df_input.columns or 'cccd' in df_input.columns:
        col_name = 'CCCD' if 'CCCD' in df_input.columns else 'cccd'
        search_by = 'cccd'
    elif 'Họ tên' in df_input.columns or 'ho_ten' in df_input.columns:
        col_name = 'Họ tên' if 'Họ tên' in df_input.columns else 'ho_ten'
        search_by = 'ho_ten'
    elif 'input' in df_input.columns:
        col_name = 'input'
        search_by = 'auto'
    else:
        col_name = df_input.columns[0]
        search_by = 'auto'

    # Pre-process database cho tra cứu nhanh
    db_names = df_db['ho_ten'].tolist()

    # Tạo Name -> CCCD mapping (O(1) lookup)
    df_unique = df_db.drop_duplicates(subset=['ho_ten'], keep='first')
    name_to_cccd = dict(zip(df_unique['ho_ten'], df_unique['cccd']))

    # CCCD set cho tra cứu chính xác và map CCCD -> Họ tên
    db_cccd_set = set(df_db['cccd'].astype(str))
    cccd_to_name = dict(zip(df_db['cccd'].astype(str), df_db['ho_ten']))

    records = df_input.to_dict('records')
    n = len(records)
    results = [None] * n

    # Danh sách các query cần fuzzy name matching để xử lý batch bằng cdist
    fuzzy_queries = []
    fuzzy_indexes = []

    # Pass 1: xử lý CCCD + thu thập các query fuzzy
    for idx, row in enumerate(records):
        raw_val = row.get(col_name)
        input_value = str(raw_val).strip() if raw_val is not None else ""

        if not input_value:
            results[idx] = {
                'input': '',
                'matched': '',
                'cccd': '',
                'status': '❌ Không có dữ liệu',
                'score': 0,
                'alternatives': []
            }
            continue

        # Xác định loại search
        if search_by == 'auto':
            if input_value.isdigit() and len(input_value) == 12:
                current_search = 'cccd'
            else:
                current_search = 'ho_ten'
        else:
            current_search = search_by

        if current_search == 'cccd':
            # Tìm chính xác CCCD - O(1) lookup
            if input_value in db_cccd_set:
                results[idx] = {
                    'input': input_value,
                    'matched': cccd_to_name.get(input_value, ''),
                    'cccd': input_value,
                    'status': '✅ Khớp chính xác',
                    'score': 100,
                    'alternatives': []
                }
            else:
                results[idx] = {
                    'input': input_value,
                    'matched': '',
                    'cccd': '',
                    'status': '❌ Không tìm thấy',
                    'score': 0,
                    'alternatives': []
                }
        else:
            # Ghi nhận để fuzzy match theo batch
            fuzzy_queries.append(input_value)
            fuzzy_indexes.append(idx)

    # Pass 2: xử lý fuzzy matching theo batch
    if fuzzy_queries:
        if FUZZY_MODULE_AVAILABLE:
            # Sử dụng batch_screen từ fuzzy_matching module (đã tối ưu bên trong)
            screen_results = batch_screen(
                fuzzy_queries,
                db_names,
                threshold=THRESHOLD_SUSPECT  # 80%
            )

            for local_idx, result in enumerate(screen_results):
                global_idx = fuzzy_indexes[local_idx]
                input_value = fuzzy_queries[local_idx]

                if result and result.get('matched'):
                    matched_name = result['matched']
                    cccd = name_to_cccd.get(matched_name, '')

                    results[global_idx] = {
                        'input': input_value,
                        'matched': matched_name,
                        'cccd': cccd,
                        'status': result['status'],
                        'score': result['score'],
                        'alternatives': result.get('alternatives', [])
                    }
                else:
                    results[global_idx] = {
                        'input': input_value,
                        'matched': '',
                        'cccd': '',
                        'status': '❌ Không tìm thấy',
                        'score': 0,
                        'alternatives': []
                    }
        elif RAPIDFUZZ_AVAILABLE:
            # Fallback: dùng rapidfuzz.process.cdist cho batch, có score_cutoff
            try:
                import numpy as np  # type: ignore
            except ImportError:
                np = None

            # cdist trả về ma trận điểm (len(fuzzy_queries) x len(db_names))
            score_matrix = fuzz_process.cdist(
                fuzzy_queries,
                db_names,
                scorer=fuzz.token_set_ratio,
                score_cutoff=80,  # lọc trước các match <80
            )

            for qi, global_idx in enumerate(fuzzy_indexes):
                input_value = fuzzy_queries[qi]
                row_scores = score_matrix[qi]

                if hasattr(row_scores, "max"):
                    max_score = row_scores.max()
                else:
                    max_score = max(row_scores) if row_scores else 0

                if max_score >= 80:
                    # Lấy index của match tốt nhất
                    if hasattr(row_scores, "argmax"):
                        best_j = int(row_scores.argmax())
                    else:
                        best_j = int(row_scores.index(max_score))

                    matched_name = db_names[best_j]
                    cccd = name_to_cccd.get(matched_name, '')

                    if max_score >= 95:
                        status = '✅ Khớp chính xác'
                    else:
                        status = '⚠️ Nghi vấn - cần kiểm tra'

                    results[global_idx] = {
                        'input': input_value,
                        'matched': matched_name,
                        'cccd': cccd,
                        'status': status,
                        'score': int(max_score),
                        'alternatives': []
                    }
                else:
                    results[global_idx] = {
                        'input': input_value,
                        'matched': '',
                        'cccd': '',
                        'status': '❌ Không tìm thấy',
                        'score': int(max_score) if max_score else 0,
                        'alternatives': []
                    }
        else:
            # Không có module fuzzy nào khả dụng (đã xử lý ở đầu hàm)
            pass

    # Loại bỏ None (nếu có) và trả về list kết quả
    return [r for r in results if r is not None]


def display_screening_results(results):
    """Hiển thị kết quả rà soát với chi tiết đầy đủ"""
    if not results:
        st.warning("Không có kết quả")
        return

    df_results = pd.DataFrame(results)

    # Thống kê
    st.markdown("---")
    st.markdown("### 📊 Kết quả rà soát")

    col1, col2, col3, col4 = st.columns(4)

    exact_match = len([r for r in results if '✅' in r['status']])
    suspicious = len([r for r in results if '⚠️' in r['status']])
    not_found = len([r for r in results if '❌' in r['status']])
    total = len(results)

    col1.metric("📋 Tổng số", total)
    col2.metric("✅ Khớp chính xác", exact_match)
    col3.metric("⚠️ Nghi vấn (≥80%)", suspicious)
    col4.metric("❌ Không tìm thấy", not_found)

    st.markdown("---")

    # Tabs cho các loại kết quả
    tab_all, tab_suspect, tab_exact, tab_notfound = st.tabs([
        f"📋 Tất cả ({total})",
        f"⚠️ Nghi vấn ({suspicious})",
        f"✅ Khớp ({exact_match})",
        f"❌ Không tìm thấy ({not_found})"
    ])

    def render_table(data):
        if not data:
            st.info("Không có dữ liệu")
            return
        df = pd.DataFrame(data)
        # Remove alternatives column for display
        if 'alternatives' in df.columns:
            df = df.drop(columns=['alternatives'])
        df_display = df.rename(columns={
            'input': 'Đầu vào',
            'matched': 'Kết quả khớp',
            'cccd': 'CCCD',
            'status': 'Trạng thái',
            'score': 'Độ tương đồng (%)'
        })
        st.dataframe(df_display, use_container_width=True, hide_index=True)

    with tab_all:
        render_table(results)

    with tab_suspect:
        suspect_results = [r for r in results if '⚠️' in r['status']]
        render_table(suspect_results)

        # Hiển thị chi tiết alternatives nếu có
        if suspect_results:
            st.markdown("#### 🔍 Chi tiết nghi vấn")
            for r in suspect_results:
                if r.get('alternatives'):
                    with st.expander(f"📌 {r['input']} → {r['matched']} ({r['score']}%)"):
                        st.write("**Các kết quả khớp khác:**")
                        for alt in r['alternatives']:
                            st.write(f"  - {alt['name']} ({alt['score']}%)")

    with tab_exact:
        exact_results = [r for r in results if '✅' in r['status']]
        render_table(exact_results)

    with tab_notfound:
        notfound_results = [r for r in results if '❌' in r['status']]
        render_table(notfound_results)

    st.markdown("---")

    # Export
    col_exp1, col_exp2 = st.columns(2)

    with col_exp1:
        # Export all
        export_df = pd.DataFrame(results)
        if 'alternatives' in export_df.columns:
            export_df = export_df.drop(columns=['alternatives'])
        st.download_button(
            label="📥 Xuất toàn bộ kết quả (CSV)",
            data=sanitize_dataframe_for_csv(export_df).to_csv(index=False).encode('utf-8-sig'),
            file_name=f"ket_qua_ra_soat_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )

    with col_exp2:
        # Export only suspicious
        suspect_results = [r for r in results if '⚠️' in r['status']]
        if suspect_results:
            suspect_df = pd.DataFrame(suspect_results)
            if 'alternatives' in suspect_df.columns:
                suspect_df = suspect_df.drop(columns=['alternatives'])
            st.download_button(
                label="⚠️ Xuất chỉ các nghi vấn (CSV)",
                data=sanitize_dataframe_for_csv(suspect_df).to_csv(index=False).encode('utf-8-sig'),
                file_name=f"nghi_van_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )


# ============================================
# COMPARE TWO NAMES TOOL
# ============================================

def show_compare_tool():
    """Tool so sánh 2 tên trực tiếp"""
    st.markdown("### 🔬 So sánh 2 tên")
    st.caption("Công cụ đánh giá độ tương đồng giữa 2 tên (Pattern: thefuzz)")

    col1, col2 = st.columns(2)

    with col1:
        name1 = st.text_input("Tên thứ nhất", placeholder="Nguyễn Văn An")

    with col2:
        name2 = st.text_input("Tên thứ hai", placeholder="Nguyễn Văn Ân")

    if st.button("🔍 So sánh", type="primary"):
        if name1 and name2:
            if FUZZY_MODULE_AVAILABLE:
                scores = compare_names(name1, name2)

                st.markdown("---")
                st.markdown("#### 📊 Kết quả so sánh")

                cols = st.columns(5)
                cols[0].metric("Ratio", f"{scores['ratio']}%")
                cols[1].metric("Partial", f"{scores['partial_ratio']}%")
                cols[2].metric("Token Sort", f"{scores['token_sort']}%")
                cols[3].metric("Token Set", f"{scores['token_set']}%")
                cols[4].metric("Weighted", f"{scores['weighted']}%")

                best = scores['best']
                status, _ = classify_match(best)

                st.markdown("---")
                st.markdown(f"### Kết luận: {status}")
                st.progress(best / 100)

                if best >= 80:
                    st.success(
                        f"✅ Độ tương đồng {best}% ≥ 80% → Có thể là cùng 1 người")
                else:
                    st.warning(f"⚠️ Độ tương đồng {best}% < 80% → Khác người")
            else:
                # Fallback
                score = fuzz.token_set_ratio(name1.lower(), name2.lower())
                st.metric("Độ tương đồng", f"{score}%")
        else:
            st.warning("Vui lòng nhập cả 2 tên")


# ============================================
# RA SOAT PAGE
# ============================================

def page_ra_soat():
    """Trang Rà soát - Kiểm tra danh sách hàng loạt với fuzzy matching 80%"""
    st.markdown("# 🔎 Rà soát hàng loạt")
    st.markdown("### Kiểm tra danh sách nhân sự với cơ sở dữ liệu")

    st.markdown("---")

    st.info("""
    **Tính năng rà soát sử dụng Fuzzy Matching (ngưỡng 80%):**
    - ✅ **Khớp chính xác** (≥95%): Tên hoàn toàn giống nhau
    - ⚠️ **Nghi vấn** (≥80%): Tên tương tự, cần kiểm tra thủ công (ví dụ: "Văn An" vs "Văn Ân")
    - ❌ **Không tìm thấy** (<80%): Không có trong database hoặc khác biệt lớn
    """)

    # Tab cho các cách nhập
    tab_upload, tab_paste, tab_compare = st.tabs([
        "📥 Upload Excel",
        "📝 Nhập trực tiếp",
        "🔬 So sánh 2 tên"
    ])

    with tab_upload:
        st.markdown("#### 📥 Upload file Excel")
        uploaded_file = st.file_uploader(
            "Chọn file Excel (cần có cột CCCD hoặc Họ tên)",
            type=["xlsx", "xls"],
            key="ra_soat_upload"
        )

        if uploaded_file:
            try:
                df_input = pd.read_excel(uploaded_file)
                st.success(f"✅ Đã đọc {len(df_input)} dòng từ file")
                st.dataframe(df_input.head(10), use_container_width=True)

                # Xử lý rà soát
                if st.button("🔍 Bắt đầu rà soát", type="primary", key="btn_ra_soat_excel"):
                    with st.spinner("Đang rà soát với ngưỡng 80%..."):
                        try:
                            results = process_batch_screening_v2(df_input)
                            display_screening_results(results)
                        except Exception as e:
                            import logging
                            logging.getLogger(__name__).error(f"Lỗi rà soát batch: {e}")
                            st.error("❌ Đã xảy ra lỗi trong quá trình rà soát. Vui lòng thử lại.")
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Lỗi đọc file Excel: {e}")
                st.error("❌ Lỗi đọc file Excel. Vui lòng đảm bảo file đúng định dạng và có cột CCCD hoặc Họ tên.")

    with tab_paste:
        st.markdown("#### 📝 Nhập danh sách trực tiếp")
        st.caption("Mỗi dòng là một CCCD hoặc Họ tên")

        input_text = st.text_area(
            "Danh sách",
            placeholder="001234567890\nNguyễn Văn A\n002345678901\n...",
            height=200
        )

        if st.button("🔍 Bắt đầu rà soát", type="primary", key="btn_ra_soat_paste"):
            if input_text.strip():
                lines = [line.strip()
                         for line in input_text.strip().split('\n') if line.strip()]
                df_input = pd.DataFrame({'input': lines})

                with st.spinner("Đang rà soát với ngưỡng 80%..."):
                    results = process_batch_screening_v2(df_input)
                    display_screening_results(results)
            else:
                st.warning("⚠️ Vui lòng nhập danh sách!")

    with tab_compare:
        show_compare_tool()
