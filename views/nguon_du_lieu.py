# -*- coding: utf-8 -*-
"""
Quản lý Nguồn dữ liệu - Security Profile 360
Theo dõi provenance của dữ liệu (OSINT Pattern)
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_connection
from auth import is_super_admin


def get_all_nguon_du_lieu():
    """Lấy danh sách tất cả nguồn dữ liệu."""
    conn = get_connection()
    try:
        df = pd.read_sql_query("""
            SELECT id, ten_nguon, loai_nguon, thoi_gian_import, 
                   nguoi_import, file_goc, ghi_chu
            FROM nguon_du_lieu
            ORDER BY thoi_gian_import DESC
        """, conn)
        return df
    except:
        return pd.DataFrame()
    finally:
        conn.close()


def add_nguon_du_lieu(ten_nguon, loai_nguon, nguoi_import, file_goc="", ghi_chu=""):
    """Thêm nguồn dữ liệu mới."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO nguon_du_lieu (ten_nguon, loai_nguon, nguoi_import, file_goc, ghi_chu)
            VALUES (?, ?, ?, ?, ?)
        """, (ten_nguon, loai_nguon, nguoi_import, file_goc, ghi_chu))
        conn.commit()
        return True, "Đã thêm nguồn dữ liệu thành công"
    except Exception as e:
        return False, f"Lỗi: {e}"
    finally:
        conn.close()


def delete_nguon_du_lieu(nguon_id):
    """Xóa nguồn dữ liệu."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM nguon_du_lieu WHERE id = ?", (nguon_id,))
        conn.commit()
        return True, "Đã xóa nguồn dữ liệu"
    except Exception as e:
        return False, f"Lỗi: {e}"
    finally:
        conn.close()


def page_nguon_du_lieu():
    """Trang quản lý nguồn dữ liệu."""

    user = st.session_state.get('user', {})

    # Chỉ Super Admin mới có quyền
    if not is_super_admin(user):
        st.error("⛔ Bạn không có quyền truy cập trang này!")
        return

    st.markdown("# 📦 Quản lý Nguồn dữ liệu")
    st.markdown("### Theo dõi nguồn gốc và provenance của dữ liệu")

    st.markdown("---")

    # Tabs
    tab_list, tab_add = st.tabs(["📋 Danh sách nguồn", "➕ Thêm nguồn mới"])

    with tab_list:
        df = get_all_nguon_du_lieu()

        if df.empty:
            st.info("💡 Chưa có nguồn dữ liệu nào được ghi nhận.")
        else:
            # Metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Tổng số nguồn", len(df))

            loai_counts = df['loai_nguon'].value_counts()
            if len(loai_counts) > 0:
                col2.metric("Loại phổ biến", loai_counts.index[0])

            # Display table
            st.markdown("#### 📋 Danh sách nguồn dữ liệu")

            # Format datetime
            if 'thoi_gian_import' in df.columns:
                df['thoi_gian_import'] = pd.to_datetime(
                    df['thoi_gian_import']).dt.strftime('%d/%m/%Y %H:%M')

            # Rename columns for display
            df_display = df.rename(columns={
                'id': 'ID',
                'ten_nguon': 'Tên nguồn',
                'loai_nguon': 'Loại nguồn',
                'thoi_gian_import': 'Thời gian import',
                'nguoi_import': 'Người import',
                'file_goc': 'File gốc',
                'ghi_chu': 'Ghi chú'
            })

            st.dataframe(df_display, use_container_width=True, hide_index=True)

            # Delete section
            st.markdown("---")
            st.markdown("#### 🗑️ Xóa nguồn dữ liệu")

            nguon_options = {row['id']: f"{row['ten_nguon']} ({row['thoi_gian_import']})"
                             for _, row in df.iterrows()}

            if nguon_options:
                selected_id = st.selectbox(
                    "Chọn nguồn để xóa",
                    options=list(nguon_options.keys()),
                    format_func=lambda x: nguon_options[x]
                )

                if st.button("🗑️ Xóa nguồn đã chọn", type="secondary"):
                    success, msg = delete_nguon_du_lieu(selected_id)
                    if success:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    with tab_add:
        st.markdown("#### ➕ Thêm nguồn dữ liệu mới")

        with st.form("add_nguon_form"):
            ten_nguon = st.text_input(
                "Tên nguồn dữ liệu *",
                placeholder="VD: Import Excel từ CA huyện Thanh Ba"
            )

            loai_nguon = st.selectbox(
                "Loại nguồn",
                options=["Excel Import", "Nhập tay",
                         "Từ đơn vị khác", "Xác minh", "Khác"]
            )

            col1, col2 = st.columns(2)

            with col1:
                nguoi_import = st.text_input(
                    "Người import",
                    value=user.get('ho_ten', '')
                )

            with col2:
                file_goc = st.text_input(
                    "Tên file gốc (nếu có)",
                    placeholder="vd: danh_sach_2024.xlsx"
                )

            ghi_chu = st.text_area(
                "Ghi chú",
                placeholder="Thông tin bổ sung về nguồn dữ liệu..."
            )

            if st.form_submit_button("✅ Thêm nguồn", type="primary"):
                if not ten_nguon:
                    st.error("⚠️ Vui lòng nhập tên nguồn!")
                else:
                    success, msg = add_nguon_du_lieu(
                        ten_nguon, loai_nguon, nguoi_import, file_goc, ghi_chu
                    )
                    if success:
                        st.success(f"✅ {msg}")
                        st.balloons()
                    else:
                        st.error(f"❌ {msg}")
