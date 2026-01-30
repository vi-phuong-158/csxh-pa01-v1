# -*- coding: utf-8 -*-
"""
Module Authentication - Security Profile 360
Xử lý đăng nhập, phân quyền, quản lý tài khoản
"""
import bcrypt
import sqlite3
import os
import secrets
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from database import get_connection
import logging

logger = logging.getLogger(__name__)

# Roles
ROLE_SUPER_ADMIN = 'super_admin'
ROLE_USER = 'user'

# Default Super Admin credentials
DEFAULT_ADMIN_USERNAME = 'admin'


def hash_password(password: str) -> str:
    """Mã hóa mật khẩu với bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Kiểm tra mật khẩu có đúng không."""
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8')
        )
    except Exception as e:
        logger.error(f"Lỗi verify password: {e}")
        return False


def authenticate(username: str, password: str) -> Optional[Dict]:
    """
    Xác thực đăng nhập.

    Returns:
        Dict với thông tin user nếu thành công, None nếu thất bại
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, password_hash, ho_ten, role, is_active, must_change_password
            FROM users 
            WHERE username = ? AND is_active = 1
        """, (username,))

        row = cursor.fetchone()

        if row and verify_password(password, row['password_hash']):
            # Cập nhật last_login
            cursor.execute("""
                UPDATE users SET last_login = ? WHERE id = ?
            """, (datetime.now(), row['id']))
            conn.commit()

            return {
                'id': row['id'],
                'username': row['username'],
                'ho_ten': row['ho_ten'] or row['username'],
                'role': row['role'],
                'must_change_password': bool(row['must_change_password'])
            }

        return None
    except Exception as e:
        logger.error(f"Lỗi authenticate: {e}")
        return None
    finally:
        conn.close()


def create_user(
    username: str,
    password: str,
    ho_ten: str = "",
    role: str = ROLE_USER,
    must_change_password: bool = False
) -> Tuple[bool, str]:
    """
    Tạo tài khoản mới.

    Returns:
        (success, message)
    """
    if not username or not password:
        return False, "Username và password không được trống"

    if len(password) < 6:
        return False, "Mật khẩu phải có ít nhất 6 ký tự"

    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Kiểm tra username đã tồn tại chưa
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            return False, f"Username '{username}' đã tồn tại"

        # Tạo user mới
        password_hash = hash_password(password)
        cursor.execute("""
            INSERT INTO users (username, password_hash, ho_ten, role, must_change_password)
            VALUES (?, ?, ?, ?, ?)
        """, (username, password_hash, ho_ten, role, int(must_change_password)))

        conn.commit()
        logger.info(f"Đã tạo user: {username} (role: {role})")
        return True, f"Đã tạo tài khoản '{username}' thành công"

    except Exception as e:
        logger.error(f"Lỗi tạo user: {e}")
        return False, f"Lỗi tạo tài khoản: {e}"
    finally:
        conn.close()


def delete_user(user_id: int) -> Tuple[bool, str]:
    """
    Xóa tài khoản (soft delete - set is_active = 0).

    Returns:
        (success, message)
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Không cho xóa super_admin cuối cùng
        cursor.execute("""
            SELECT COUNT(*) FROM users 
            WHERE role = ? AND is_active = 1 AND id != ?
        """, (ROLE_SUPER_ADMIN, user_id))

        admin_count = cursor.fetchone()[0]

        cursor.execute(
            "SELECT role, username FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()

        if not user:
            return False, "Không tìm thấy tài khoản"

        if user['role'] == ROLE_SUPER_ADMIN and admin_count == 0:
            return False, "Không thể xóa Super Admin cuối cùng"

        # Soft delete
        cursor.execute(
            "UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
        conn.commit()

        logger.info(f"Đã xóa user: {user['username']}")
        return True, f"Đã xóa tài khoản '{user['username']}'"

    except Exception as e:
        logger.error(f"Lỗi xóa user: {e}")
        return False, f"Lỗi xóa tài khoản: {e}"
    finally:
        conn.close()


def change_password(user_id: int, new_password: str) -> Tuple[bool, str]:
    """Đổi mật khẩu."""
    if len(new_password) < 6:
        return False, "Mật khẩu phải có ít nhất 6 ký tự"

    conn = get_connection()
    try:
        cursor = conn.cursor()
        password_hash = hash_password(new_password)

        cursor.execute("""
            UPDATE users 
            SET password_hash = ?, must_change_password = 0
            WHERE id = ?
        """, (password_hash, user_id))

        conn.commit()
        return True, "Đổi mật khẩu thành công"
    except Exception as e:
        logger.error(f"Lỗi đổi mật khẩu: {e}")
        return False, f"Lỗi đổi mật khẩu: {e}"
    finally:
        conn.close()


def get_all_users() -> List[Dict]:
    """Lấy danh sách tất cả users (chỉ active)."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, ho_ten, role, created_at, last_login
            FROM users 
            WHERE is_active = 1
            ORDER BY created_at DESC
        """)

        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Lỗi lấy danh sách users: {e}")
        return []
    finally:
        conn.close()


def init_super_admin():
    """
    Tạo Super Admin mặc định nếu chưa có user nào.
    Được gọi khi khởi động app.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Kiểm tra đã có user nào chưa
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]

        if count == 0:
            # Get password from env or generate random
            env_password = os.environ.get('ADMIN_PASSWORD')
            if env_password:
                password = env_password
                is_generated = False
            else:
                password = secrets.token_urlsafe(16)
                is_generated = True

            # Tạo super admin mặc định
            password_hash = hash_password(password)
            cursor.execute("""
                INSERT INTO users (username, password_hash, ho_ten, role, must_change_password)
                VALUES (?, ?, ?, ?, ?)
            """, (
                DEFAULT_ADMIN_USERNAME,
                password_hash,
                'Administrator',
                ROLE_SUPER_ADMIN,
                1  # Bắt buộc đổi mật khẩu lần đầu
            ))
            conn.commit()
            logger.info(
                f"Đã tạo Super Admin mặc định: {DEFAULT_ADMIN_USERNAME}")

            if is_generated:
                print("="*60)
                print(f"[SECURITY NOTICE] Generated Random Super Admin Password")
                print(f"Username: {DEFAULT_ADMIN_USERNAME}")
                print(f"Password: {password}")
                print(f"Please change this password immediately after logging in.")
                print("="*60)
            else:
                print(
                    f"[i] Super Admin initialized with provided environment password.")
    except Exception as e:
        logger.error(f"Lỗi init super admin: {e}")
    finally:
        conn.close()


def is_super_admin(user: Dict) -> bool:
    """Kiểm tra user có phải Super Admin không."""
    if not user:
        return False
    return user.get('role') == ROLE_SUPER_ADMIN
