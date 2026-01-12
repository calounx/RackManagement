"""
Authentication and authorization module for HomeRack API.
Provides JWT-based authentication and role-based access control.
"""

from .jwt import create_access_token, create_refresh_token, decode_token
from .security import verify_password, get_password_hash, validate_password
from .deps import get_current_user, get_current_active_user, require_role

__all__ = [
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "verify_password",
    "get_password_hash",
    "validate_password",
    "get_current_user",
    "get_current_active_user",
    "require_role",
]
