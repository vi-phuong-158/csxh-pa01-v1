# -*- coding: utf-8 -*-
"""
Authentication Service - Raw SQLite Implementation
Quản lý xác thực và người dùng bằng sqlite3 thuần túy.
"""
import bcrypt
import os
import secrets
import logging
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from database import get_connection

logger = logging.getLogger(__name__)

# Roles
ROLE_SUPER_ADMIN = 'super_admin'
ROLE_USER = 'user'
DEFAULT_ADMIN_USERNAME = 'admin'


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception as e:
        logger.error(f"Lỗi verify password: {e}")
        return False


def authenticate(username: str, password: str) -> Optional[Dict]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, password_hash, ho_ten, role, must_change_password "
            "FROM users WHERE username = ? AND is_active = 1",
            (username,)
        )
        user = cursor.fetchone()

        if user and verify_password(password, user['password_hash']):
            cursor.execute(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.now().isoformat(), user['id'])
            )
            conn.commit()
            return {
                'id': user['id'],
                'username': user['username'],
                'ho_ten': user['ho_ten'] or user['username'],
                'role': user['role'],
                'must_change_password': bool(user['must_change_password'])
            }
        return None
    except Exception as e:
        logger.error(f"Lỗi authenticate: {e}")
        return None
    finally:
        conn.close()


def create_user(username: str, password: str, ho_ten: str = "", role: str = ROLE_USER, must_change_password: bool = False) -> Tuple[bool, str]:
    if not username or not password:
        return False, "Username và password không được trống"
    if len(password) < 6:
        return False, "Mật khẩu phải có ít nhất 6 ký tự"

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            return False, f"Username '{username}' đã tồn tại"

        password_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, password_hash, ho_ten, role, must_change_password, is_active) "
            "VALUES (?, ?, ?, ?, ?, 1)",
            (username, password_hash, ho_ten, role, int(must_change_password))
        )
        conn.commit()
        logger.info(f"Đã tạo user: {username} (role: {role})")
        return True, f"Đã tạo tài khoản '{username}' thành công"
    except Exception as e:
        logger.error(f"Lỗi tạo user: {e}")
        return False, "Đã xảy ra lỗi khi tạo tài khoản. Vui lòng thử lại."
    finally:
        conn.close()


def delete_user(user_id: int) -> Tuple[bool, str]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()

        if not user:
            return False, "Không tìm thấy tài khoản"

        cursor.execute(
            "SELECT COUNT(id) as cnt FROM users WHERE role = ? AND is_active = 1 AND id != ?",
            (ROLE_SUPER_ADMIN, user_id)
        )
        admin_count = cursor.fetchone()['cnt']

        if user['role'] == ROLE_SUPER_ADMIN and admin_count == 0:
            return False, "Không thể xóa Super Admin cuối cùng"

        cursor.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
        conn.commit()
        return True, f"Đã xóa tài khoản '{user['username']}'"
    except Exception as e:
        logger.error(f"Lỗi xóa user: {e}")
        return False, "Đã xảy ra lỗi khi xóa tài khoản. Vui lòng thử lại."
    finally:
        conn.close()


def change_password(user_id: int, new_password: str) -> Tuple[bool, str]:
    if len(new_password) < 6:
        return False, "Mật khẩu phải có ít nhất 6 ký tự"

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            return False, "Không tìm thấy tài khoản"

        password_hash = hash_password(new_password)
        cursor.execute(
            "UPDATE users SET password_hash = ?, must_change_password = 0 WHERE id = ?",
            (password_hash, user_id)
        )
        conn.commit()
        return True, "Đổi mật khẩu thành công"
    except Exception as e:
        logger.error(f"Lỗi đổi mật khẩu: {e}")
        return False, "Đã xảy ra lỗi khi đổi mật khẩu. Vui lòng thử lại."
    finally:
        conn.close()


def get_all_users() -> List[Dict]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, ho_ten, role, created_at, last_login "
            "FROM users WHERE is_active = 1 ORDER BY created_at DESC"
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Lỗi lấy danh sách users: {e}")
        return []
    finally:
        conn.close()


def init_super_admin():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(id) as cnt FROM users")
        count = cursor.fetchone()['cnt']

        if count == 0:
            env_password = os.environ.get('ADMIN_PASSWORD')
            if env_password:
                password = env_password
            else:
                password = secrets.token_urlsafe(16)

            password_hash = hash_password(password)
            cursor.execute(
                "INSERT INTO users (username, password_hash, ho_ten, role, must_change_password, is_active) "
                "VALUES (?, ?, ?, ?, 1, 1)",
                (DEFAULT_ADMIN_USERNAME, password_hash, 'Administrator', ROLE_SUPER_ADMIN)
            )
            conn.commit()

            logger.info(f"Đã tạo Super Admin mặc định: {DEFAULT_ADMIN_USERNAME}")
            if not env_password:
                # Ghi mật khẩu vào log thay vì stdout để tránh lộ lọt
                logger.warning(
                    f"[SECURITY] Mật khẩu Super Admin được tạo tự động. "
                    f"Username: {DEFAULT_ADMIN_USERNAME}, Password: {password}"
                )
    except Exception as e:
        logger.error(f"Lỗi init super admin: {e}")
    finally:
        conn.close()


def is_super_admin(user: Dict) -> bool:
    if not user:
        return False
    return user.get('role') == ROLE_SUPER_ADMIN
