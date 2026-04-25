import bcrypt
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from backend.models.models import User, AuditLog

logger = logging.getLogger(__name__)

ROLE_SUPER_ADMIN = "super_admin"
ROLE_USER = "user"
DEFAULT_ADMIN_USERNAME = "admin"
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 5


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception as e:
        logger.error(f"Lỗi verify password: {e}")
        return False


def validate_password_policy(password: str) -> Tuple[bool, str]:
    if not password or len(password) < 8:
        return False, "Mật khẩu phải có ít nhất 8 ký tự"
    if not any(c.isupper() for c in password):
        return False, "Mật khẩu phải có ít nhất 1 chữ hoa"
    if not any(c.islower() for c in password):
        return False, "Mật khẩu phải có ít nhất 1 chữ thường"
    if not any(c.isdigit() for c in password):
        return False, "Mật khẩu phải có ít nhất 1 chữ số"
    if not any(not c.isalnum() for c in password):
        return False, "Mật khẩu phải có ít nhất 1 ký tự đặc biệt"
    return True, ""


def authenticate(db: Session, username: str, password: str) -> Optional[Dict]:
    stmt = select(User).where(User.username == username, User.is_active == 1)
    user = db.execute(stmt).scalar_one_or_none()

    if not user:
        return None

    now = datetime.now()

    # Kiểm tra lockout
    if user.lockout_until and now < user.lockout_until:
        return None

    if verify_password(password, user.password_hash):
        user.failed_login_attempts = 0
        user.lockout_until = None
        user.last_login = now
        db.commit()
        return {
            "id": user.id,
            "username": user.username,
            "ho_ten": user.ho_ten or user.username,
            "role": user.role,
            "must_change_password": bool(user.must_change_password),
        }

    # Sai mật khẩu
    user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
    if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
        user.lockout_until = now + timedelta(minutes=LOCKOUT_MINUTES)
        _add_audit(db, user.username, "LOGIN_LOCK", str(user.id),
                   f"Bị khóa sau {user.failed_login_attempts} lần sai")
    db.commit()
    return None


def create_user(
    db: Session,
    username: str,
    password: str,
    ho_ten: str = "",
    role: str = ROLE_USER,
    must_change_password: bool = False,
) -> Tuple[bool, str]:
    if not username or not password:
        return False, "Username và password không được trống"
    ok, msg = validate_password_policy(password)
    if not ok:
        return False, msg

    if db.execute(select(User).where(User.username == username)).scalar_one_or_none():
        return False, f"Username '{username}' đã tồn tại"

    db.add(User(
        username=username,
        password_hash=hash_password(password),
        ho_ten=ho_ten,
        role=role,
        must_change_password=int(must_change_password),
    ))
    db.commit()
    return True, f"Đã tạo tài khoản '{username}'"


def delete_user(db: Session, user_id: int) -> Tuple[bool, str]:
    user = db.get(User, user_id)
    if not user:
        return False, "Không tìm thấy tài khoản"

    admin_count = db.execute(
        select(func.count(User.id)).where(
            User.role == ROLE_SUPER_ADMIN, User.is_active == 1, User.id != user_id
        )
    ).scalar_one()

    if user.role == ROLE_SUPER_ADMIN and admin_count == 0:
        return False, "Không thể xóa Super Admin cuối cùng"

    user.is_active = 0
    db.commit()
    return True, f"Đã vô hiệu hóa tài khoản '{user.username}'"


def change_password(db: Session, user_id: int, new_password: str) -> Tuple[bool, str]:
    ok, msg = validate_password_policy(new_password)
    if not ok:
        return False, msg

    user = db.get(User, user_id)
    if not user:
        return False, "Không tìm thấy tài khoản"

    user.password_hash = hash_password(new_password)
    user.must_change_password = 0
    db.commit()
    return True, "Đổi mật khẩu thành công"


def get_all_users(db: Session) -> List[Dict]:
    users = db.execute(
        select(User).where(User.is_active == 1).order_by(User.created_at.desc())
    ).scalars().all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "ho_ten": u.ho_ten,
            "role": u.role,
            "created_at": u.created_at,
            "last_login": u.last_login,
        }
        for u in users
    ]


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.get(User, user_id)


def init_super_admin(db: Session):
    count = db.execute(select(func.count(User.id))).scalar_one()
    if count > 0:
        return

    from backend.config import settings
    password = settings.ADMIN_PASSWORD or secrets.token_urlsafe(16)
    db.add(User(
        username=DEFAULT_ADMIN_USERNAME,
        password_hash=hash_password(password),
        ho_ten="Administrator",
        role=ROLE_SUPER_ADMIN,
        must_change_password=1,
    ))
    db.commit()
    logger.info(f"Đã tạo Super Admin mặc định: {DEFAULT_ADMIN_USERNAME}")


def is_super_admin(user: Dict) -> bool:
    return bool(user) and user.get("role") == ROLE_SUPER_ADMIN


def _add_audit(db: Session, nguoi: str, hanh_dong: str, khoa: str, mo_ta: str):
    try:
        db.add(AuditLog(
            bang="users",
            hanh_dong=hanh_dong,
            khoa_chinh=khoa,
            du_lieu_moi=mo_ta,
            nguoi_thuc_hien=nguoi,
        ))
    except Exception:
        pass
