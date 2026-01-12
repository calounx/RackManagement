#!/usr/bin/env python3
"""
Create initial admin user for HomeRack application.

This script creates a default admin user that can be used to bootstrap
the authentication system. The default credentials should be changed
immediately after first login.

Default credentials:
  Email: admin@homerack.local
  Password: Admin123!

Usage:
  python scripts/create_admin_user.py

Or with custom credentials:
  python scripts/create_admin_user.py --email admin@example.com --password YourPassword123!
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, engine
from app.models import Base, User, UserRole
from app.auth.security import get_password_hash, validate_password
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_admin_user(email: str, password: str, full_name: str = "System Administrator"):
    """
    Create an admin user in the database.

    Args:
        email: Admin user email
        password: Admin user password
        full_name: Admin user full name
    """
    # Validate password
    is_valid, error_message = validate_password(password)
    if not is_valid:
        logger.error(f"Password validation failed: {error_message}")
        sys.exit(1)

    # Create database session
    db = SessionLocal()

    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            logger.warning(f"User with email {email} already exists")
            response = input("Do you want to reset the password? (yes/no): ")
            if response.lower() == 'yes':
                existing_user.hashed_password = get_password_hash(password)
                existing_user.role = UserRole.ADMIN
                existing_user.is_active = True
                existing_user.updated_at = datetime.utcnow()
                db.commit()
                logger.info(f"Admin user password reset: {email}")
            else:
                logger.info("Operation cancelled")
            return

        # Create admin user
        hashed_password = get_password_hash(password)
        admin_user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=UserRole.ADMIN,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        logger.info(f"Admin user created successfully!")
        logger.info(f"  Email: {email}")
        logger.info(f"  Role: {admin_user.role}")
        logger.info(f"  Please change the password after first login!")

    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create admin user for HomeRack application"
    )
    parser.add_argument(
        "--email",
        default="admin@homerack.local",
        help="Admin user email (default: admin@homerack.local)"
    )
    parser.add_argument(
        "--password",
        default="Admin123!",
        help="Admin user password (default: Admin123!)"
    )
    parser.add_argument(
        "--full-name",
        default="System Administrator",
        help="Admin user full name (default: System Administrator)"
    )

    args = parser.parse_args()

    logger.info("Creating admin user...")
    logger.info(f"Email: {args.email}")

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    create_admin_user(args.email, args.password, args.full_name)


if __name__ == "__main__":
    main()
