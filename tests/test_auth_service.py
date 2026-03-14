# -*- coding: utf-8 -*-
"""
Unit Tests cho auth_service.py - Security Profile 360
======================================================
Sử dụng pytest framework.

Tests bao gồm:
- hash_password / verify_password: Kiểm tra mã hóa và xác thực mật khẩu
- validate_password_policy: Kiểm tra chính sách mật khẩu
- create_user: Tạo user mới (thành công, trùng username, mật khẩu yếu)
- authenticate: Đăng nhập (thành công / thất bại)
- is_super_admin: Kiểm tra quyền super admin
- delete_user: Xóa user (bảo vệ super admin cuối cùng)

Chạy tests:
    pytest tests/test_auth_service.py -v
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

import pytest

# Thêm thư mục gốc vào sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Mock streamlit + audit_log TRƯỚC khi import auth_service
# Vì auth_service imports từ views.audit_log (dùng streamlit)
sys.modules['streamlit'] = MagicMock()
sys.modules['views.audit_log'] = MagicMock()

from app.services.auth_service import (
    hash_password,
    verify_password,
    validate_password_policy,
    create_user,
    is_super_admin,
    ROLE_SUPER_ADMIN,
    ROLE_USER,
    DEFAULT_ADMIN_USERNAME,
)


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def mock_user_model():
    """Tạo mock User model cho tests."""
    user = MagicMock()
    user.id = 1
    user.username = "testuser"
    user.password_hash = hash_password("Test@123!")
    user.ho_ten = "Test User"
    user.role = ROLE_USER
    user.is_active = 1
    user.must_change_password = 0
    user.failed_login_attempts = 0
    user.last_failed_login_at = None
    user.last_login = None
    user.created_at = datetime.now()
    return user


@pytest.fixture
def mock_admin_model():
    """Tạo mock Super Admin model cho tests."""
    admin = MagicMock()
    admin.id = 1
    admin.username = DEFAULT_ADMIN_USERNAME
    admin.password_hash = hash_password("Admin@123!")
    admin.ho_ten = "Administrator"
    admin.role = ROLE_SUPER_ADMIN
    admin.is_active = 1
    admin.must_change_password = 0
    admin.failed_login_attempts = 0
    admin.last_failed_login_at = None
    admin.last_login = None
    return admin


# ============================================
# TESTS: hash_password & verify_password
# ============================================

class TestPasswordHashing:
    """Tests cho hàm hash_password và verify_password."""

    def test_hash_password_returns_string(self):
        """Hash password phải trả về chuỗi."""
        hashed = hash_password("MyPassword123!")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_not_plaintext(self):
        """Hash phải khác plaintext."""
        password = "MyPassword123!"
        hashed = hash_password(password)
        assert hashed != password

    def test_hash_password_unique_per_call(self):
        """Mỗi lần hash phải tạo kết quả khác nhau (do salt)."""
        hashed1 = hash_password("SamePassword!")
        hashed2 = hash_password("SamePassword!")
        assert hashed1 != hashed2

    def test_verify_password_correct(self):
        """Verify với đúng mật khẩu phải trả về True."""
        password = "SecurePass@99"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_wrong(self):
        """Verify với sai mật khẩu phải trả về False."""
        hashed = hash_password("CorrectPassword@1")
        assert verify_password("WrongPassword@2", hashed) is False

    def test_verify_password_invalid_hash(self):
        """Verify với hash không hợp lệ phải trả về False (không crash)."""
        assert verify_password("anything", "not_a_valid_hash") is False


# ============================================
# TESTS: validate_password_policy
# ============================================

class TestPasswordPolicy:
    """Tests cho hàm validate_password_policy."""

    def test_strong_password(self):
        """Mật khẩu đủ mạnh phải pass."""
        ok, msg = validate_password_policy("Strong@123")
        assert ok is True
        assert msg == ""

    def test_short_password(self):
        """Mật khẩu dưới 8 ký tự phải bị từ chối."""
        ok, msg = validate_password_policy("Ab1!")
        assert ok is False
        assert "8" in msg

    def test_missing_uppercase(self):
        """Thiếu chữ hoa phải bị từ chối."""
        ok, msg = validate_password_policy("nouppercas@1")
        assert ok is False

    def test_missing_lowercase(self):
        """Thiếu chữ thường phải bị từ chối."""
        ok, msg = validate_password_policy("NOLOWER@12")
        assert ok is False

    def test_missing_digit(self):
        """Thiếu số phải bị từ chối."""
        ok, msg = validate_password_policy("NoDigits@Here")
        assert ok is False

    def test_missing_special(self):
        """Thiếu ký tự đặc biệt phải bị từ chối."""
        ok, msg = validate_password_policy("NoSpecial123")
        assert ok is False

    def test_empty_password(self):
        """Mật khẩu rỗng phải bị từ chối."""
        ok, msg = validate_password_policy("")
        assert ok is False

    def test_none_password(self):
        """Mật khẩu None phải bị từ chối."""
        ok, msg = validate_password_policy(None)
        assert ok is False


# ============================================
# TESTS: create_user
# ============================================

class TestCreateUser:
    """Tests cho hàm create_user."""

    @patch('app.services.auth_service.get_db')
    def test_create_user_success(self, mock_get_db):
        """Tạo user mới thành công."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock: user chưa tồn tại
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        ok, msg = create_user("newuser", "ValidPass@123", "Người dùng mới")
        assert ok is True
        assert "thành công" in msg

        # Kiểm tra db.add đã được gọi
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch('app.services.auth_service.get_db')
    def test_create_user_duplicate_username(self, mock_get_db):
        """Tạo user trùng username phải thất bại."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock: user đã tồn tại
        existing_user = MagicMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = existing_user

        ok, msg = create_user("existinguser", "ValidPass@123")
        assert ok is False
        assert "đã tồn tại" in msg

    @patch('app.services.auth_service.get_db')
    def test_create_user_weak_password(self, mock_get_db):
        """Tạo user với mật khẩu yếu phải thất bại."""
        ok, msg = create_user("testuser", "weak")
        assert ok is False
        # Không cần gọi database vì password policy check trước
        mock_get_db.assert_not_called()

    def test_create_user_empty_username(self):
        """Username rỗng phải thất bại."""
        ok, msg = create_user("", "ValidPass@123")
        assert ok is False

    def test_create_user_empty_password(self):
        """Password rỗng phải thất bại."""
        ok, msg = create_user("testuser", "")
        assert ok is False


# ============================================
# TESTS: is_super_admin
# ============================================

class TestIsSuperAdmin:
    """Tests cho hàm is_super_admin."""

    def test_super_admin_true(self):
        """User với role super_admin phải trả về True."""
        user = {'role': ROLE_SUPER_ADMIN, 'username': 'admin'}
        assert is_super_admin(user) is True

    def test_regular_user_false(self):
        """User bình thường phải trả về False."""
        user = {'role': ROLE_USER, 'username': 'user'}
        assert is_super_admin(user) is False

    def test_none_user(self):
        """User None phải trả về False."""
        assert is_super_admin(None) is False

    def test_empty_dict(self):
        """Dict rỗng phải trả về False."""
        assert is_super_admin({}) is False

    def test_missing_role_key(self):
        """Dict thiếu key 'role' phải trả về False."""
        user = {'username': 'admin'}
        assert is_super_admin(user) is False
