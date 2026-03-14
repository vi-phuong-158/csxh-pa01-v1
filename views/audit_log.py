# -*- coding: utf-8 -*-
"""
Audit Log Viewer - Security Profile 360
Xem lịch sử thay đổi dữ liệu
"""
import logging
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import get_connection
from app.services.auth_service import is_super_admin
from utils.security_utils import sanitize_dataframe_for_csv

logger = logging.getLogger(__name__)


def get_audit_logs(limit=100, table_filter=None, action_filter=None, date_from=None, date_to=None):
    """Lấy audit logs với các bộ lọc."""
    conn = get_connection()
    try:
        query = """
            SELECT id, bang, hanh_dong, khoa_chinh, 
                   du_lieu_cu, du_lieu_moi, 
                   nguoi_thuc_hien, ip_address, created_at
            FROM audit_log
            WHERE 1=1
        """
        params = []

        if table_filter and table_filter != "Tất cả":
            query += " AND bang = ?"
            params.append(table_filter)

        if action_filter and action_filter != "Tất cả":
            query += " AND hanh_dong = ?"
            params.append(action_filter)

        if date_from:
            query += " AND DATE(created_at) >= ?"
            params.append(date_from.strftime('%Y-%m-%d'))

        if date_to:
            query += " AND DATE(created_at) <= ?"
            params.append(date_to.strftime('%Y-%m-%d'))

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Lỗi truy vấn: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def get_table_list():
    """Lấy danh sách các bảng có trong audit log."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT bang FROM audit_log")
        tables = [row[0] for row in cursor.fetchall()]
        return ["Tất cả"] + tables
    except Exception as e:
        logger.warning(f"Lỗi lấy danh sách bảng audit: {e}")
        return ["Tất cả"]
    finally:
        conn.close()


def get_action_list():
    """Lấy danh sách các loại hành động."""
    return ["Tất cả", "INSERT", "UPDATE", "DELETE", "VIEW"]


def get_client_ip(request_headers: dict | None = None) -> str:
    """
    Lấy IP thực của client.
    Ưu tiên header X-Forwarded-For (khi chạy sau reverse proxy), fallback về REMOTE_ADDR.
    """
    headers = request_headers or {}
    xff = headers.get("X-Forwarded-For") or headers.get("x-forwarded-for")
    if xff:
        # Có thể chứa danh sách IP, lấy IP đầu tiên
        return xff.split(",")[0].strip()

    # Streamlit không expose REMOTE_ADDR trực tiếp; có thể bổ sung qua context khác nếu cần
    return headers.get("REMOTE_ADDR", "unknown")


def add_audit_log(bang, hanh_dong, khoa_chinh, du_lieu_cu=None, du_lieu_moi=None, nguoi_thuc_hien=None, ip_address: str | None = None):
    """Thêm một entry vào audit log."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_log (bang, hanh_dong, khoa_chinh, du_lieu_cu, du_lieu_moi, nguoi_thuc_hien, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            bang,
            hanh_dong,
            khoa_chinh,
            du_lieu_cu,
            du_lieu_moi,
            nguoi_thuc_hien,
            ip_address or "unknown",
        ))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Lỗi ghi audit log: {e}")
        return False
    finally:
        conn.close()


def page_audit_log():
    """Trang xem lịch sử thay đổi."""

    user = st.session_state.get('user', {})

    # Chỉ Super Admin
    if not is_super_admin(user):
        st.error("⛔ Bạn không có quyền truy cập trang này!")
        return

    st.markdown("# 📜 Lịch sử thay đổi")
    st.markdown("### Audit Log - Theo dõi mọi thay đổi trong hệ thống")

    st.markdown("---")

    # Filters
    st.markdown("#### 🔍 Bộ lọc")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        table_filter = st.selectbox(
            "Bảng",
            options=get_table_list()
        )

    with col2:
        action_filter = st.selectbox(
            "Hành động",
            options=get_action_list()
        )

    with col3:
        date_from = st.date_input(
            "Từ ngày",
            value=datetime.now() - timedelta(days=30)
        )

    with col4:
        date_to = st.date_input(
            "Đến ngày",
            value=datetime.now()
        )

    limit = st.slider("Số bản ghi tối đa", 50, 500, 100, 50)

    st.markdown("---")

    # Load data
    df = get_audit_logs(
        limit=limit,
        table_filter=table_filter,
        action_filter=action_filter,
        date_from=date_from,
        date_to=date_to
    )

    if df.empty:
        st.info("💡 Chưa có log nào trong khoảng thời gian này.")
        st.caption("Audit log sẽ được ghi khi có thao tác thay đổi dữ liệu.")
        return

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📋 Tổng bản ghi", len(df))

    if 'hanh_dong' in df.columns:
        insert_count = len(df[df['hanh_dong'] == 'INSERT'])
        update_count = len(df[df['hanh_dong'] == 'UPDATE'])
        delete_count = len(df[df['hanh_dong'] == 'DELETE'])

        col2.metric("➕ INSERT", insert_count)
        col3.metric("✏️ UPDATE", update_count)
        col4.metric("🗑️ DELETE", delete_count)

    st.markdown("---")

    # Format display
    if 'created_at' in df.columns:
        df['created_at'] = pd.to_datetime(
            df['created_at']).dt.strftime('%d/%m/%Y %H:%M:%S')

    # Rename columns
    df_display = df.rename(columns={
        'id': 'ID',
        'bang': 'Bảng',
        'hanh_dong': 'Hành động',
        'khoa_chinh': 'Khóa chính',
        'du_lieu_cu': 'Dữ liệu cũ',
        'du_lieu_moi': 'Dữ liệu mới',
        'nguoi_thuc_hien': 'Người thực hiện',
        'ip_address': 'IP',
        'created_at': 'Thời gian'
    })

    # Color-code by action
    st.markdown("#### 📋 Chi tiết Audit Log")

    # Tabs by action type
    tab_all, tab_insert, tab_update, tab_delete = st.tabs([
        f"📋 Tất cả ({len(df)})",
        f"➕ INSERT ({len(df[df['hanh_dong'] == 'INSERT']) if 'hanh_dong' in df.columns else 0})",
        f"✏️ UPDATE ({len(df[df['hanh_dong'] == 'UPDATE']) if 'hanh_dong' in df.columns else 0})",
        f"🗑️ DELETE ({len(df[df['hanh_dong'] == 'DELETE']) if 'hanh_dong' in df.columns else 0})"
    ])

    with tab_all:
        st.dataframe(df_display, use_container_width=True, hide_index=True)

    with tab_insert:
        df_insert = df_display[df_display['Hành động'] ==
                               'INSERT'] if 'Hành động' in df_display.columns else pd.DataFrame()
        if not df_insert.empty:
            st.dataframe(df_insert, use_container_width=True, hide_index=True)
        else:
            st.info("Không có bản ghi INSERT trong khoảng thời gian này.")

    with tab_update:
        df_update = df_display[df_display['Hành động'] ==
                               'UPDATE'] if 'Hành động' in df_display.columns else pd.DataFrame()
        if not df_update.empty:
            st.dataframe(df_update, use_container_width=True, hide_index=True)
        else:
            st.info("Không có bản ghi UPDATE trong khoảng thời gian này.")

    with tab_delete:
        df_delete = df_display[df_display['Hành động'] ==
                               'DELETE'] if 'Hành động' in df_display.columns else pd.DataFrame()
        if not df_delete.empty:
            st.dataframe(df_delete, use_container_width=True, hide_index=True)
        else:
            st.info("Không có bản ghi DELETE trong khoảng thời gian này.")

    # Export
    st.markdown("---")
    st.download_button(
        label="📥 Xuất Audit Log (CSV)",
        data=sanitize_dataframe_for_csv(df).to_csv(index=False).encode('utf-8-sig'),
        file_name=f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )
