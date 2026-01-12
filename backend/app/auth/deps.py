"""
Authentication dependencies for FastAPI endpoints.
Provides dependency injection for current user and role checking.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..config import settings
from .jwt import decode_token

# OAuth2 scheme for token extraction
# tokenUrl is the endpoint where clients can get tokens
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    auto_error=False  # Don't automatically error if token is missing (allows optional auth)
)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get the current authenticated user from the JWT token.

    Args:
        token: JWT token from Authorization header
        db: Database session

    Returns:
        User object if authenticated, None otherwise (when REQUIRE_AUTH is False)

    Raises:
        HTTPException: If token is invalid or user not found (when REQUIRE_AUTH is True)
    """
    # If auth is not required and no token provided, return None
    if not settings.REQUIRE_AUTH and not token:
        return None

    # If auth is required but no token provided, raise error
    if settings.REQUIRE_AUTH and not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Decode token
    payload = decode_token(token)
    if not payload:
        if settings.REQUIRE_AUTH:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None

    # Check token type
    token_type = payload.get("type")
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Use access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user_id: int = payload.get("sub")
    if not user_id:
        if settings.REQUIRE_AUTH:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        if settings.REQUIRE_AUTH:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None

    return user


async def get_current_active_user(
    current_user: Optional[User] = Depends(get_current_user)
) -> Optional[User]:
    """
    Get the current active user (not disabled).

    Args:
        current_user: Current user from get_current_user dependency

    Returns:
        Active user object

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user:
        if settings.REQUIRE_AUTH:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        return None

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return current_user


def require_role(*allowed_roles: str):
    """
    Dependency factory for role-based access control.

    Usage:
        @app.get("/admin/users", dependencies=[Depends(require_role("admin"))])
        async def list_users():
            ...

    Args:
        allowed_roles: Roles that are allowed to access the endpoint

    Returns:
        Dependency function that checks user role
    """
    async def check_role(current_user: User = Depends(get_current_active_user)):
        if not current_user:
            if settings.REQUIRE_AUTH:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated"
                )
            return None

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}"
            )

        return current_user

    return check_role


# Convenience dependencies for common roles
require_admin = require_role("admin")
require_user = require_role("admin", "user")
