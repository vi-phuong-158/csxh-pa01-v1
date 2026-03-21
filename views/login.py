# -*- coding: utf-8 -*-
"""
Login Page - Security Profile 360
Giao diện đăng nhập và đổi mật khẩu
"""
import streamlit as st
from app.services.auth_service import authenticate, change_password, is_super_admin
from pathlib import Path


def show_login_form():
    """Hiển thị form đăng nhập."""

    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        logo_path = Path("logo.png")
        if logo_path.exists():
            # Sử dụng columns để thu nhỏ logo và căn giữa
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                st.image(str(logo_path), use_container_width=True)
            
        st.markdown("""
        <div style="text-align: center; padding: 0px 20px 0px 20px;">
            <h1 style="margin-top: 0; font-size: 20px; line-height: 1.2;">Security Profile 360</h1>
            <p style="color: #aaa; font-size: 13px;">Hệ thống quản lý hồ sơ an ninh</p>
        </div>
        <div style="height: 1px; background-color: #333; margin: 10px 0;"></div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            st.markdown("<h3 style='margin-bottom: -15px;'>Đăng nhập</h3>", unsafe_allow_html=True)

            username = st.text_input(
                "👤 Tên đăng nhập",
                placeholder="Nhập username"
            )

            password = st.text_input(
                "🔑 Mật khẩu",
                type="password",
                placeholder="Nhập mật khẩu"
            )

            submitted = st.form_submit_button(
                "🔓 Đăng nhập", type="primary", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.error("⚠️ Vui lòng nhập đầy đủ thông tin!")
                else:
                    user = authenticate(username, password)

                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user = user
                        st.success(f"✅ Chào mừng, {user['ho_ten']}!")
                        st.rerun()
                    else:
                        st.error("❌ Sai tên đăng nhập hoặc mật khẩu!")


def show_change_password_form():
    """Hiển thị form bắt buộc đổi mật khẩu (lần đầu đăng nhập)."""

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        logo_path = Path("logo.png")
        if logo_path.exists():
            # Sử dụng columns để thu nhỏ logo và căn giữa
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                st.image(str(logo_path), use_container_width=True)
            
        st.markdown("""
        <div style="text-align: center; padding: 0px 20px 0px 20px;">
            <h1 style="margin-top: 0; font-size: 20px; line-height: 1.2;">Đổi mật khẩu</h1>
            <p style="color: #ffc107; font-size: 13px;">⚠️ Bạn cần đổi mật khẩu trước khi tiếp tục</p>
        </div>
        <div style="height: 1px; background-color: #333; margin: 10px 0;"></div>
        """, unsafe_allow_html=True)

        with st.form("change_password_form"):
            new_password = st.text_input(
                "🔑 Mật khẩu mới",
                type="password",
                placeholder="Ít nhất 6 ký tự"
            )

            confirm_password = st.text_input(
                "🔑 Xác nhận mật khẩu mới",
                type="password",
                placeholder="Nhập lại mật khẩu"
            )

            submitted = st.form_submit_button(
                "✅ Đổi mật khẩu", type="primary", use_container_width=True)

            if submitted:
                if not new_password or not confirm_password:
                    st.error("⚠️ Vui lòng nhập đầy đủ!")
                elif new_password != confirm_password:
                    st.error("❌ Mật khẩu không khớp!")
                elif len(new_password) < 6:
                    st.error("⚠️ Mật khẩu phải có ít nhất 6 ký tự!")
                else:
                    user = st.session_state.user
                    success, msg = change_password(user['id'], new_password)

                    if success:
                        st.session_state.user['must_change_password'] = False
                        st.success("✅ Đổi mật khẩu thành công!")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")


def show_user_menu():
    """Hiển thị menu user ở sidebar."""
    user = st.session_state.get('user', {})

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"👤 **{user.get('ho_ten', 'User')}**")

    role_display = "🔑 Super Admin" if is_super_admin(user) else "👤 User"
    st.sidebar.caption(role_display)

    # Nút đổi mật khẩu
    if st.sidebar.button("🔐 Đổi mật khẩu", use_container_width=True):
        st.session_state.show_change_password = True
        st.rerun()

    # Nút đăng xuất
    if st.sidebar.button("🚪 Đăng xuất", use_container_width=True):
        logout()
        st.rerun()


def show_self_change_password():
    """Form đổi mật khẩu tự nguyện (không bắt buộc)."""
    st.markdown("### 🔐 Đổi mật khẩu")

    with st.form("self_change_password"):
        current_password = st.text_input(
            "Mật khẩu hiện tại",
            type="password"
        )

        new_password = st.text_input(
            "Mật khẩu mới",
            type="password",
            placeholder="Ít nhất 6 ký tự"
        )

        confirm_password = st.text_input(
            "Xác nhận mật khẩu mới",
            type="password"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.form_submit_button("✅ Đổi mật khẩu", type="primary"):
                # Verify current password
                user = st.session_state.user
                check_user = authenticate(user['username'], current_password)

                if not check_user:
                    st.error("❌ Mật khẩu hiện tại không đúng!")
                elif new_password != confirm_password:
                    st.error("❌ Mật khẩu mới không khớp!")
                elif len(new_password) < 6:
                    st.error("⚠️ Mật khẩu phải có ít nhất 6 ký tự!")
                else:
                    success, msg = change_password(user['id'], new_password)
                    if success:
                        st.success("✅ Đổi mật khẩu thành công!")
                        st.session_state.show_change_password = False
                    else:
                        st.error(f"❌ {msg}")

        with col2:
            if st.form_submit_button("❌ Hủy"):
                st.session_state.show_change_password = False
                st.rerun()


def logout():
    """Đăng xuất."""
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.show_change_password = False


def is_logged_in() -> bool:
    """Kiểm tra đã đăng nhập chưa."""
    return st.session_state.get('logged_in', False)


def get_current_user():
    """Lấy thông tin user hiện tại."""
    return st.session_state.get('user', None)


def require_login():
    """
    Decorator/helper để yêu cầu đăng nhập.
    Trả về True nếu đã đăng nhập, False nếu chưa (và hiện form login).
    """
    if not is_logged_in():
        show_login_form()
        return False

    # Kiểm tra phải đổi mật khẩu không
    user = st.session_state.user
    if user.get('must_change_password'):
        show_change_password_form()
        return False

    return True
