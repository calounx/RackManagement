"""
Common dependencies for API endpoints.
Provides database session management and pagination utilities.
"""

from typing import Generator
from fastapi import Depends, Query
from sqlalchemy.orm import Session
from ..database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def pagination_params(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return")
) -> dict:
    """
    Pagination parameters dependency.

    Args:
        skip: Number of records to skip (offset)
        limit: Maximum number of records to return

    Returns:
        Dictionary with skip and limit values
    """
    return {"skip": skip, "limit": limit}
