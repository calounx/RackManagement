#!/usr/bin/env python3
"""
Database initialization script.
Creates all database tables from SQLAlchemy models.
"""
import sys
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models import Base
from app.database import engine

def init_database():
    """Initialize database by creating all tables."""
    print("Initializing database...")
    print(f"Database URL: {engine.url}")

    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")

        # Print created tables
        tables = Base.metadata.tables.keys()
        print(f"\nCreated {len(tables)} tables:")
        for table in sorted(tables):
            print(f"  - {table}")

        return True
    except Exception as e:
        print(f"Error initializing database: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
