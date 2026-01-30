
import bcrypt
import os
import secrets
import logging
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from sqlalchemy import select, func
from app.db.session import SessionLocal
from app.models.models import User

logger = logging.getLogger(__name__)

# Roles
ROLE_SUPER_ADMIN = 'super_admin'
ROLE_USER = 'user'
DEFAULT_ADMIN_USERNAME = 'admin'


def get_db():
    return SessionLocal()


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
    db = get_db()
    try:
        stmt = select(User).where(User.username ==
                                  username, User.is_active == 1)
        user = db.execute(stmt).scalar_one_or_none()

        if user and verify_password(password, user.password_hash):
            user.last_login = datetime.now()
            db.commit()
            return {
                'id': user.id,
                'username': user.username,
                'ho_ten': user.ho_ten or user.username,
                'role': user.role,
                'must_change_password': bool(user.must_change_password)
            }
        return None
    except Exception as e:
        logger.error(f"Lỗi authenticate: {e}")
        return None
    finally:
        db.close()


def create_user(username: str, password: str, ho_ten: str = "", role: str = ROLE_USER, must_change_password: bool = False) -> Tuple[bool, str]:
    if not username or not password:
        return False, "Username và password không được trống"
    if len(password) < 6:
        return False, "Mật khẩu phải có ít nhất 6 ký tự"

    db = get_db()
    try:
        stmt = select(User).where(User.username == username)
        if db.execute(stmt).scalar_one_or_none():
            return False, f"Username '{username}' đã tồn tại"

        password_hash = hash_password(password)
        new_user = User(
            username=username,
            password_hash=password_hash,
            ho_ten=ho_ten,
            role=role,
            must_change_password=int(must_change_password)
        )
        db.add(new_user)
        db.commit()
        logger.info(f"Đã tạo user: {username} (role: {role})")
        return True, f"Đã tạo tài khoản '{username}' thành công"
    except Exception as e:
        db.rollback()
        logger.error(f"Lỗi tạo user: {e}")
        return False, f"Lỗi tạo tài khoản: {e}"
    finally:
        db.close()


def delete_user(user_id: int) -> Tuple[bool, str]:
    db = get_db()
    try:
        stmt = select(User).where(User.id == user_id)
        user = db.execute(stmt).scalar_one_or_none()

        if not user:
            return False, "Không tìm thấy tài khoản"

        # Check super admin count
        stmt_count = select(func.count(User.id)).where(
            User.role == ROLE_SUPER_ADMIN, User.is_active == 1, User.id != user_id)
        admin_count = db.execute(stmt_count).scalar_one()

        if user.role == ROLE_SUPER_ADMIN and admin_count == 0:
            return False, "Không thể xóa Super Admin cuối cùng"

        user.is_active = 0
        db.commit()
        return True, f"Đã xóa tài khoản '{user.username}'"
    except Exception as e:
        db.rollback()
        logger.error(f"Lỗi xóa user: {e}")
        return False, f"Lỗi xóa tài khoản: {e}"
    finally:
        db.close()


def change_password(user_id: int, new_password: str) -> Tuple[bool, str]:
    if len(new_password) < 6:
        return False, "Mật khẩu phải có ít nhất 6 ký tự"

    db = get_db()
    try:
        user = db.get(User, user_id)
        if not user:
            return False, "User not found"

        user.password_hash = hash_password(new_password)
        user.must_change_password = 0
        db.commit()
        return True, "Đổi mật khẩu thành công"
    except Exception as e:
        db.rollback()
        logger.error(f"Lỗi đổi mật khẩu: {e}")
        return False, f"Lỗi đổi mật khẩu: {e}"
    finally:
        db.close()


def get_all_users() -> List[Dict]:
    db = get_db()
    try:
        stmt = select(User).where(User.is_active ==
                                  1).order_by(User.created_at.desc())
        users = db.execute(stmt).scalars().all()
        return [
            {
                'id': u.id,
                'username': u.username,
                'ho_ten': u.ho_ten,
                'role': u.role,
                'created_at': u.created_at,
                'last_login': u.last_login
            } for u in users
        ]
    except Exception as e:
        logger.error(f"Lỗi lấy danh sách users: {e}")
        return []
    finally:
        db.close()


def init_super_admin():
    db = get_db()
    try:
        stmt = select(func.count(User.id))
        count = db.execute(stmt).scalar_one()

        if count == 0:
            env_password = os.environ.get('ADMIN_PASSWORD')
            if env_password:
                password = env_password
                is_generated = False
            else:
                password = secrets.token_urlsafe(16)
                is_generated = True

            password_hash = hash_password(password)
            super_admin = User(
                username=DEFAULT_ADMIN_USERNAME,
                password_hash=password_hash,
                ho_ten='Administrator',
                role=ROLE_SUPER_ADMIN,
                must_change_password=1
            )
            db.add(super_admin)
            db.commit()

            logger.info(
                f"Đã tạo Super Admin mặc định: {DEFAULT_ADMIN_USERNAME}")
            if is_generated:
                print("="*60)
                print(f"[SECURITY NOTICE] Generated Random Super Admin Password")
                print(f"Username: {DEFAULT_ADMIN_USERNAME}")
                print(f"Password: {password}")
                print("="*60)
    except Exception as e:
        logger.error(f"Lỗi init super admin: {e}")
    finally:
        db.close()


def is_super_admin(user: Dict) -> bool:
    if not user:
        return False
    return user.get('role') == ROLE_SUPER_ADMIN
