# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import datetime
from utils.bulk_import import (
    create_excel_template, 
    validate_excel_data, 
    export_error_excel,
    bulk_import_all,
    TEMPLATE_DEFINITIONS
)

# Map key to readable name
IMPORT_OPTIONS = {
    "all": "📦 Trọn bộ (File 5 Sheet)",
    "doi_tuong": "👤 Thông tin đối tượng",
    "than_nhan": "👨‍👩‍👧‍👦 Thân nhân",
    "qua_trinh_hoat_dong": "⏳ Quá trình hoạt động",
    "lien_he": "📞 Liên hệ",
    "tai_chinh": "💳 Tài chính & Ngân hàng",
    "phuong_tien": "🚗 Phương tiện đi lại",
    "ho_so_dac_thu": "🌐 Hồ sơ CSXH (Đặc thù)"
}

# ============================================
# NHAP EXCEL PAGE
# ============================================
def page_nhap_excel():
    """Trang Nhập Excel - Import dữ liệu hàng loạt"""
    st.markdown("# 📥 Nhập Excel")
    st.markdown("### Import dữ liệu hàng loạt từ file Excel")
    
    st.markdown("---")
    
    # Select Import Mode
    col_mode, col_info = st.columns([1, 2])
    with col_mode:
        selected_mode_key = st.radio(
            "Chọn loại dữ liệu muốn nhập:",
            list(IMPORT_OPTIONS.keys()),
            format_func=lambda x: IMPORT_OPTIONS[x],
            help="Chọn 'Trọn bộ' để nhập file 5 sheet cũ, hoặc chọn từng mục để nhập file lẻ."
        )
    
    with col_info:
        st.info(f"""
        **Bạn đang chọn:** {IMPORT_OPTIONS[selected_mode_key]}
        
        *Hệ thống sẽ tạo file mẫu tương ứng với lựa chọn này. Vui lòng tải file mẫu, điền dữ liệu và upload lại.*
        """)

    # Option cho CSXH đặc thù
    csxh_type = None
    if selected_mode_key in ["all", "ho_so_dac_thu"]:
        with st.expander("Tùy chọn loại Hồ sơ CSXH (nếu có)", expanded=True):
            loai_csxh_options = {
                "Tổng hợp (tất cả loại)": None,
                "🤵 Hôn nhân với người nước ngoài": "Hon_Nhan_NN",
                "🏢 Làm việc cho tổ chức nước ngoài": "Lam_Viec_NN",
                "🎓 Du học/Công tác nước ngoài": "Hoc_Tap_Cong_Tac_NN",
                "⚠️ Vi phạm pháp luật ở nước ngoài": "Vi_Pham_NN",
                "🔍 Đã từng được xác minh": "Xac_Minh",
            }
            selected_csxh_label = st.selectbox("Chọn loại hình đặc thù chi tiết:", list(loai_csxh_options.keys()))
            csxh_type = loai_csxh_options[selected_csxh_label]

    st.markdown("---")
    
    # ===== BƯỚC 1: TẢI FILE MẪU =====
    st.markdown("#### 📄 Bước 1: Tải file mẫu")
    
    # Generate template
    template_data = create_excel_template(import_type=selected_mode_key, csxh_type=csxh_type)
    file_name = f"mau_{selected_mode_key}.xlsx"
    if csxh_type:
        file_name = f"mau_{selected_mode_key}_{csxh_type}.xlsx"
    
    st.download_button(
        label=f"📥 Tải file mẫu: {IMPORT_OPTIONS[selected_mode_key]}",
        data=template_data,
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        key=f"dl_btn_{selected_mode_key}"
    )
    
    st.markdown("---")
    
    # ===== BƯỚC 2: UPLOAD FILE =====
    st.markdown("#### 📤 Bước 2: Upload file Excel đã điền")
    
    uploaded_file = st.file_uploader(
        "Chọn file Excel",
        type=["xlsx", "xls"],
        key=f"uploader_{selected_mode_key}"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ Đã tải lên: **{uploaded_file.name}**")
        
        st.markdown("---")
        
        # ===== BƯỚC 3: VALIDATE & PREVIEW =====
        st.markdown(f"#### 🔍 Bước 3: Kiểm tra dữ liệu ({IMPORT_OPTIONS[selected_mode_key]})")
        
        with st.spinner("Đang đọc và kiểm tra dữ liệu..."):
            # Validate with specific context
            validation_results = validate_excel_data(uploaded_file, import_type=selected_mode_key)
        
        # Calculate stats
        total_valid = sum(r['valid_count'] for r in validation_results.values())
        total_errors = sum(len(r['errors']) for r in validation_results.values())
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("✅ Bản ghi hợp lệ", total_valid)
        with col2:
            st.metric("❌ Lỗi phát hiện", total_errors)
            
        # Error file download
        if total_errors > 0:
            error_excel = export_error_excel(validation_results)
            if error_excel:
                st.download_button(
                    "📥 Tải file báo lỗi chi tiết",
                    data=error_excel,
                    file_name="baocao_loi.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="secondary"
                )

        # Show details based on mode
        st.markdown("##### 📋 Chi tiết dữ liệu:")
        
        # Helper to render tab content
        def render_tab_content(key_name, label):
            res = validation_results[key_name]
            st.caption(f"**{label}**: {res['valid_count']} hợp lệ | {len(res['errors'])} lỗi")
            
            if res['errors']:
                with st.expander(f"⚠️ Xem {len(res['errors'])} lỗi", expanded=True):
                    for err in res['errors'][:10]:
                        st.error(err)
                    if len(res['errors']) > 10:
                        st.warning(f"... và {len(res['errors']) - 10} lỗi khác")
                        
            if res['data'] is not None and not res['data'].empty:
                st.dataframe(res['data'].head(), use_container_width=True)
            elif res['valid_count'] == 0 and not res['errors']:
                st.info("Không có dữ liệu.")

        # If ALL, show Tabs. If Single, show just that section.
        if selected_mode_key == 'all':
            tabs = st.tabs([
                "👤 Đối tượng", "📞 Liên hệ", "👨‍👩‍👧‍👦 Thân nhân", 
                "💳 Tài chính", "🚗 Phương tiện", "🌐 CSXH", "⏳ Quá trình"
            ])
            with tabs[0]: render_tab_content('doi_tuong', "Đối tượng")
            with tabs[1]: render_tab_content('lien_he', "Liên hệ")
            with tabs[2]: render_tab_content('than_nhan', "Thân nhân")
            with tabs[3]: render_tab_content('tai_chinh', "Tài chính")
            with tabs[4]: render_tab_content('phuong_tien', "Phương tiện")
            with tabs[5]: render_tab_content('ho_so_dac_thu', "Hồ sơ CSXH")
            with tabs[6]: render_tab_content('qua_trinh_hoat_dong', "Quá trình HĐ")
            
        else:
            # Single mode
            render_tab_content(selected_mode_key, IMPORT_OPTIONS[selected_mode_key])

        # ===== BƯỚC 4: IMPORT =====
        st.markdown("---")
        st.markdown("#### 💾 Bước 4: Lưu vào cơ sở dữ liệu")
        
        if total_valid > 0:
            if total_errors > 0:
                st.warning(f"⚠️ Đang có {total_errors} dòng lỗi. Hệ thống sẽ CHỈ LƯU {total_valid} dòng hợp lệ.")
            
            if st.button("🚀 Thực hiện Import", type="primary"):
                with st.spinner("Đang lưu vào database..."):
                    success, msg, stats = bulk_import_all(validation_results)
                    
                    if success:
                        st.success(msg)
                        # Display detailed stats
                        cols = st.columns(len([k for k,v in stats.items() if v > 0]) or 1)
                        idx = 0
                        for k, v in stats.items():
                            if v > 0:
                                with cols[idx]:
                                    st.metric(k.replace('_', ' ').title(), f"+{v}")
                                idx += 1
                        st.balloons()
                    else:
                        st.error(msg)
        else:
            st.error("🚫 Không có dữ liệu hợp lệ nào để import.")
