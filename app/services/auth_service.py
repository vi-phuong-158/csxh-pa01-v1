
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


def validate_password_policy(password: str) -> Tuple[bool, str]:
    """
    Chính sách mật khẩu:
    - Tối thiểu 8 ký tự
    - Có chữ hoa, chữ thường, số và ký tự đặc biệt
    """
    if not password or len(password) < 8:
        return False, "Mật khẩu phải có ít nhất 8 ký tự"

    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)

    if not (has_upper and has_lower and has_digit and has_special):
        return False, "Mật khẩu phải có chữ hoa, chữ thường, số và ký tự đặc biệt"

    return True, ""

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception as e:
        logger.error(f"Lỗi verify password: {e}")
        return False

def authenticate(username: str, password: str) -> Optional[Dict]:
    db = get_db()
    try:
        stmt = select(User).where(User.username == username, User.is_active == 1)
        user = db.execute(stmt).scalar_one_or_none()
        
        if user and verify_password(password, user.password_hash):
            # Reset failed attempts on successful login
            user.failed_login_attempts = 0
            user.last_failed_login_at = None
            user.last_login = datetime.now()
            db.commit()
            return {
                'id': user.id,
                'username': user.username,
                'ho_ten': user.ho_ten or user.username,
                'role': user.role,
                'must_change_password': bool(user.must_change_password)
            }

        # Handle failed login logic (including lockout)
        if user:
            now = datetime.now()
            # Initialize counters if null
            if getattr(user, "failed_login_attempts", None) is None:
                user.failed_login_attempts = 0
                user.last_failed_login_at = None

            # If account is currently locked (5+ fails within last 5 minutes)
            if (
                user.failed_login_attempts >= 5
                and user.last_failed_login_at
                and (now - user.last_failed_login_at).total_seconds() < 5 * 60
            ):
                from views.audit_log import add_audit_log
                add_audit_log(
                    bang="users",
                    hanh_dong="LOGIN_LOCK",
                    khoa_chinh=str(user.id),
                    du_lieu_cu=None,
                    du_lieu_moi="Tài khoản bị khóa tạm thời do đăng nhập sai quá số lần cho phép",
                    nguoi_thuc_hien=user.username,
                    ip_address="unknown",
                )
                db.commit()
                return None

            # Increase failed attempts
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            user.last_failed_login_at = now

            # If this failure reaches threshold, add audit log
            if user.failed_login_attempts >= 5:
                from views.audit_log import add_audit_log
                add_audit_log(
                    bang="users",
                    hanh_dong="LOGIN_LOCK",
                    khoa_chinh=str(user.id),
                    du_lieu_cu=None,
                    du_lieu_moi=f"Tài khoản bị khóa tạm thời sau {user.failed_login_attempts} lần đăng nhập sai",
                    nguoi_thuc_hien=user.username,
                    ip_address="unknown",
                )

            db.commit()

        return None
    except Exception as e:
        logger.error(f"Lỗi authenticate: {e}")
        return None
    finally:
        db.close()

def create_user(username: str, password: str, ho_ten: str = "", role: str = ROLE_USER, must_change_password: bool = False) -> Tuple[bool, str]:
    if not username or not password:
        return False, "Username và password không được trống"
    ok, msg = validate_password_policy(password)
    if not ok:
        return False, msg
        
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
        stmt_count = select(func.count(User.id)).where(User.role == ROLE_SUPER_ADMIN, User.is_active == 1, User.id != user_id)
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
    ok, msg = validate_password_policy(new_password)
    if not ok:
        return False, msg
        
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
        stmt = select(User).where(User.is_active == 1).order_by(User.created_at.desc())
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
            
            logger.info(f"Đã tạo Super Admin mặc định: {DEFAULT_ADMIN_USERNAME}")
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
