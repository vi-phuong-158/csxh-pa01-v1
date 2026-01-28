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

def get_database_names():
    """Lấy danh sách họ tên từ database"""
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

    for idx, row in df_input.iterrows():
        input_value = str(row[col_name]).strip()

        if not input_value:
            continue

        # Xác định loại search
        if search_by == 'auto':
            if input_value.isdigit() and len(input_value) == 12:
                current_search = 'cccd'
            else:
                current_search = 'ho_ten'
        else:
            current_search = search_by

        # Tìm kiếm
        if current_search == 'cccd':
            # Tìm chính xác CCCD
            match = df_db[df_db['cccd'] == input_value]
            if not match.empty:
                results.append({
                    'input': input_value,
                    'matched': match.iloc[0]['ho_ten'],
                    'cccd': match.iloc[0]['cccd'],
                    'status': '✅ Khớp chính xác',
                    'score': 100,
                    'alternatives': []
                })
            else:
                results.append({
                    'input': input_value,
                    'matched': '',
                    'cccd': '',
                    'status': '❌ Không tìm thấy',
                    'score': 0,
                    'alternatives': []
                })
        else:
            # Fuzzy matching họ tên - sử dụng module mới
            if FUZZY_MODULE_AVAILABLE:
                # Sử dụng batch_screen từ fuzzy_matching module
                screen_results = batch_screen(
                    [input_value],
                    df_db['ho_ten'].tolist(),
                    threshold=THRESHOLD_SUSPECT  # 80%
                )

                if screen_results and screen_results[0]['matched']:
                    result = screen_results[0]
                    # Tìm CCCD tương ứng
                    matched_row = df_db[df_db['ho_ten'] == result['matched']]
                    cccd = matched_row.iloc[0]['cccd'] if not matched_row.empty else ''

                    results.append({
                        'input': input_value,
                        'matched': result['matched'],
                        'cccd': cccd,
                        'status': result['status'],
                        'score': result['score'],
                        'alternatives': result.get('alternatives', [])
                    })
                else:
                    results.append({
                        'input': input_value,
                        'matched': '',
                        'cccd': '',
                        'status': '❌ Không tìm thấy',
                        'score': 0,
                        'alternatives': []
                    })
            else:
                # Fallback to rapidfuzz directly
                match_result = fuzz_process.extractOne(
                    input_value,
                    df_db['ho_ten'].tolist(),
                    scorer=fuzz.token_set_ratio
                )

                if match_result and match_result[1] >= 80:  # 80% threshold
                    matched_row = df_db[df_db['ho_ten'] == match_result[0]]
                    cccd = matched_row.iloc[0]['cccd'] if not matched_row.empty else ''

                    if match_result[1] >= 95:
                        status = '✅ Khớp chính xác'
                    else:
                        status = '⚠️ Nghi vấn - cần kiểm tra'

                    results.append({
                        'input': input_value,
                        'matched': match_result[0],
                        'cccd': cccd,
                        'status': status,
                        'score': match_result[1],
                        'alternatives': []
                    })
                else:
                    results.append({
                        'input': input_value,
                        'matched': match_result[0] if match_result else '',
                        'cccd': '',
                        'status': '❌ Không tìm thấy',
                        'score': match_result[1] if match_result else 0,
                        'alternatives': []
                    })

    return results


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
                        results = process_batch_screening_v2(df_input)
                        display_screening_results(results)
            except Exception as e:
                st.error(f"❌ Lỗi đọc file: {e}")

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
