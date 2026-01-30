# -*- coding: utf-8 -*-
"""
User Management Page - Security Profile 360
Quản lý tài khoản (chỉ Super Admin)
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from app.services.auth_service import (
    create_user,
    delete_user,
    change_password,
    get_all_users,
    is_super_admin,
    ROLE_SUPER_ADMIN,
    ROLE_USER
)


def page_quan_ly_user():
    """Trang quản lý tài khoản - Chỉ Super Admin."""

    user = st.session_state.get('user', {})

    # Kiểm tra quyền
    if not is_super_admin(user):
        st.error("⛔ Bạn không có quyền truy cập trang này!")
        return

    st.markdown("# 👥 Quản lý tài khoản")
    st.markdown("### Tạo, xóa và quản lý người dùng hệ thống")

    st.markdown("---")

    # Tabs
    tab_list, tab_create = st.tabs(
        ["📋 Danh sách tài khoản", "➕ Tạo tài khoản mới"])

    with tab_list:
        show_user_list()

    with tab_create:
        show_create_user_form()


def show_user_list():
    """Hiển thị danh sách users."""
    users = get_all_users()

    if not users:
        st.info("💡 Chưa có tài khoản nào.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(users)

    # Format columns
    df['role_display'] = df['role'].apply(
        lambda x: '🔑 Super Admin' if x == ROLE_SUPER_ADMIN else '👤 User'
    )

    df['created_at'] = pd.to_datetime(
        df['created_at']).dt.strftime('%d/%m/%Y %H:%M')
    df['last_login'] = pd.to_datetime(
        df['last_login']).dt.strftime('%d/%m/%Y %H:%M')
    df['last_login'] = df['last_login'].fillna('Chưa đăng nhập')

    # Display table
    st.markdown("#### 📋 Danh sách tài khoản")

    # Show metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng tài khoản", len(users))
    col2.metric("Super Admin", len(
        [u for u in users if u['role'] == ROLE_SUPER_ADMIN]))
    col3.metric("User thường", len(
        [u for u in users if u['role'] == ROLE_USER]))

    st.markdown("---")

    # Interactive table with actions
    for user in users:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])

            with col1:
                role_icon = '🔑' if user['role'] == ROLE_SUPER_ADMIN else '👤'
                st.write(f"{role_icon} **{user['username']}**")

            with col2:
                st.write(user['ho_ten'] or '-')

            with col3:
                last_login = user.get('last_login')
                if last_login:
                    # Handle both datetime objects and strings
                    if isinstance(last_login, datetime):
                        login_str = last_login.strftime('%d/%m/%Y')
                    else:
                        login_str = str(last_login)[:10]
                    st.caption(f"Đăng nhập: {login_str}")
                else:
                    st.caption("Chưa đăng nhập")

            with col4:
                # Reset password button
                if st.button("🔐", key=f"reset_{user['id']}", help="Reset mật khẩu"):
                    st.session_state.reset_user_id = user['id']
                    st.session_state.reset_username = user['username']

            with col5:
                # Don't allow deleting self
                current_user = st.session_state.get('user', {})
                if user['id'] != current_user.get('id'):
                    if st.button("🗑️", key=f"del_{user['id']}", help="Xóa tài khoản"):
                        st.session_state.delete_user_id = user['id']
                        st.session_state.delete_username = user['username']

            st.markdown("---")

    # Reset password dialog
    if st.session_state.get('reset_user_id'):
        show_reset_password_dialog()

    # Delete confirmation dialog
    if st.session_state.get('delete_user_id'):
        show_delete_confirmation_dialog()


def show_reset_password_dialog():
    """Dialog reset mật khẩu."""
    user_id = st.session_state.reset_user_id
    username = st.session_state.reset_username

    st.warning(f"⚠️ Reset mật khẩu cho **{username}**")

    with st.form("reset_password_form"):
        new_password = st.text_input(
            "Mật khẩu mới",
            type="password",
            placeholder="Ít nhất 6 ký tự"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.form_submit_button("✅ Reset", type="primary"):
                if len(new_password) >= 6:
                    success, msg = change_password(user_id, new_password)
                    if success:
                        st.success(f"✅ Đã reset mật khẩu cho {username}")
                        st.session_state.reset_user_id = None
                        st.session_state.reset_username = None
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
                else:
                    st.error("⚠️ Mật khẩu phải có ít nhất 6 ký tự!")

        with col2:
            if st.form_submit_button("❌ Hủy"):
                st.session_state.reset_user_id = None
                st.session_state.reset_username = None
                st.rerun()


def show_delete_confirmation_dialog():
    """Dialog xác nhận xóa."""
    user_id = st.session_state.delete_user_id
    username = st.session_state.delete_username

    st.error(f"⚠️ Bạn có chắc muốn xóa tài khoản **{username}**?")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Xóa", type="primary"):
            success, msg = delete_user(user_id)
            if success:
                st.success(f"✅ {msg}")
                st.session_state.delete_user_id = None
                st.session_state.delete_username = None
                st.rerun()
            else:
                st.error(f"❌ {msg}")

    with col2:
        if st.button("❌ Hủy"):
            st.session_state.delete_user_id = None
            st.session_state.delete_username = None
            st.rerun()


def show_create_user_form():
    """Form tạo tài khoản mới."""
    st.markdown("#### ➕ Tạo tài khoản mới")

    with st.form("create_user_form"):
        col1, col2 = st.columns(2)

        with col1:
            username = st.text_input(
                "👤 Username *",
                placeholder="vd: nguyenvana"
            )

            password = st.text_input(
                "🔑 Mật khẩu *",
                type="password",
                placeholder="Ít nhất 6 ký tự"
            )

        with col2:
            ho_ten = st.text_input(
                "📝 Họ tên",
                placeholder="vd: Nguyễn Văn A"
            )

            role = st.selectbox(
                "🎭 Phân quyền",
                options=[ROLE_USER, ROLE_SUPER_ADMIN],
                format_func=lambda x: '👤 User thường' if x == ROLE_USER else '🔑 Super Admin'
            )

        must_change = st.checkbox(
            "Yêu cầu đổi mật khẩu khi đăng nhập lần đầu", value=True)

        submitted = st.form_submit_button("✅ Tạo tài khoản", type="primary")

        if submitted:
            if not username:
                st.error("⚠️ Username không được trống!")
            elif not password:
                st.error("⚠️ Mật khẩu không được trống!")
            elif len(password) < 6:
                st.error("⚠️ Mật khẩu phải có ít nhất 6 ký tự!")
            else:
                success, msg = create_user(
                    username=username,
                    password=password,
                    ho_ten=ho_ten,
                    role=role,
                    must_change_password=must_change
                )

                if success:
                    st.success(f"✅ {msg}")
                    st.balloons()
                else:
                    st.error(f"❌ {msg}")
