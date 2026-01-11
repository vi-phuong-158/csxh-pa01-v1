# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_connection

# Try importing rapidfuzz, handle if missing
try:
    from rapidfuzz import process as fuzz_process
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False

# ============================================
# RA SOAT PAGE
# ============================================

def process_batch_screening(df_input):
    """Xử lý rà soát với fuzzy matching"""
    if not RAPIDFUZZ_AVAILABLE:
        return [{"input": "Lỗi", "matched": "", "cccd": "", "status": "⚠️ Cần cài rapidfuzz: pip install rapidfuzz", "score": 0}]
    
    # Lấy danh sách đối tượng từ database
    conn = get_connection()
    try:
        df_db = pd.read_sql_query("SELECT cccd, ho_ten, ngay_sinh FROM doi_tuong", conn)
    finally:
        conn.close()
    
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
        search_by = 'auto'  # Tự động xác định
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
                    'score': 100
                })
            else:
                results.append({
                    'input': input_value,
                    'matched': '',
                    'cccd': '',
                    'status': '❌ Không tìm thấy',
                    'score': 0
                })
        else:
            # Fuzzy matching họ tên
            if not df_db.empty:
                match_result = fuzz_process.extractOne(
                    input_value, 
                    df_db['ho_ten'].tolist(),
                    scorer=fuzz.token_set_ratio
                )
                
                if match_result and match_result[1] >= 80:
                    matched_idx = df_db[df_db['ho_ten'] == match_result[0]].index[0]
                    results.append({
                        'input': input_value,
                        'matched': match_result[0],
                        'cccd': df_db.loc[matched_idx, 'cccd'],
                        'status': '✅ Khớp chính xác' if match_result[1] >= 95 else '⚠️ Nghi vấn',
                        'score': match_result[1]
                    })
                else:
                    results.append({
                        'input': input_value,
                        'matched': match_result[0] if match_result else '',
                        'cccd': '',
                        'status': '❌ Không tìm thấy',
                        'score': match_result[1] if match_result else 0
                    })
            else:
                results.append({
                    'input': input_value,
                    'matched': '',
                    'cccd': '',
                    'status': '❌ Database trống',
                    'score': 0
                })
    
    return results

def display_screening_results(results):
    """Hiển thị kết quả rà soát"""
    if not results:
        st.warning("Không có kết quả")
        return
    
    df_results = pd.DataFrame(results)
    
    # Thống kê
    st.markdown("---")
    st.markdown("### 📊 Kết quả rà soát")
    
    col1, col2, col3 = st.columns(3)
    
    exact_match = len([r for r in results if '✅' in r['status']])
    suspicious = len([r for r in results if '⚠️' in r['status']])
    not_found = len([r for r in results if '❌' in r['status']])
    
    col1.metric("✅ Khớp chính xác", exact_match)
    col2.metric("⚠️ Nghi vấn", suspicious)
    col3.metric("❌ Không tìm thấy", not_found)
    
    st.markdown("---")
    
    # Bảng kết quả
    df_display = df_results.rename(columns={
        'input': 'Đầu vào',
        'matched': 'Kết quả khớp',
        'cccd': 'CCCD',
        'status': 'Trạng thái',
        'score': 'Độ tương đồng (%)'
    })
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # Export
    st.download_button(
        label="📥 Xuất kết quả Excel",
        data=df_display.to_csv(index=False).encode('utf-8-sig'),
        file_name=f"ket_qua_ra_soat_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )

def page_ra_soat():
    """Trang Rà soát - Kiểm tra danh sách hàng loạt với fuzzy matching"""
    st.markdown("# 🔎 Rà soát hàng loạt")
    st.markdown("### Kiểm tra danh sách nhân sự với cơ sở dữ liệu")
    
    st.markdown("---")
    
    st.info("""
    **Tính năng rà soát cho phép:**
    - Upload file Excel danh sách cần kiểm tra
    - Hoặc nhập danh sách CCCD/Họ tên trực tiếp
    - Hệ thống sẽ đối sánh với database và hiển thị kết quả
    """)
    
    # Tab cho 2 cách nhập
    tab_upload, tab_paste = st.tabs(["📥 Upload Excel", "📝 Nhập trực tiếp"])
    
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
                    with st.spinner("Đang rà soát..."):
                        results = process_batch_screening(df_input)
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
                lines = [line.strip() for line in input_text.strip().split('\n') if line.strip()]
                df_input = pd.DataFrame({'input': lines})
                
                with st.spinner("Đang rà soát..."):
                    results = process_batch_screening(df_input)
                    display_screening_results(results)
            else:
                st.warning("⚠️ Vui lòng nhập danh sách!")
