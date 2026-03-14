"""
Backward-compatible auth module.

This file now delegates all authentication logic to the unified
SQLAlchemy-based implementation in `app.services.auth_service`.
"""

from app.services.auth_service import (  # noqa: F401
    ROLE_SUPER_ADMIN,
    ROLE_USER,
    DEFAULT_ADMIN_USERNAME,
    authenticate,
    change_password,
    create_user,
    delete_user,
    get_all_users,
    init_super_admin,
    is_super_admin,
)

