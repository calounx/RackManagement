#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script

This script migrates all data from SQLite database to PostgreSQL.
It preserves all relationships and data integrity.

Usage:
    python migrate_to_postgres.py --sqlite-path ./homerack.db --postgres-url postgresql://user:pass@host/db

Requirements:
    - Source SQLite database must exist
    - Target PostgreSQL database must exist (but can be empty)
    - All Alembic migrations must be applied to target database first
"""

import argparse
import sys
import os
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, MetaData, Table, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, IntegrityError
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def backup_sqlite_database(sqlite_path: str) -> str:
    """Create a backup of SQLite database before migration."""
    backup_path = f"{sqlite_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    try:
        import shutil
        shutil.copy2(sqlite_path, backup_path)
        logger.info(f"Created SQLite backup: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        raise


def get_table_order():
    """
    Define the order of tables for migration to respect foreign key constraints.
    Tables with no foreign keys first, then tables that depend on them.
    """
    return [
        # Independent tables (no foreign keys)
        'device_types',
        'brands',
        'dcim_connections',

        # Tables with one level of dependencies
        'models',  # depends on brands, device_types
        'device_specifications',  # depends on models (optional)

        # Tables with second level of dependencies
        'devices',  # depends on device_specifications, models
        'racks',

        # Tables with third level of dependencies
        'rack_positions',  # depends on devices, racks
        'connections',  # depends on devices
    ]


def test_database_connections(sqlite_url: str, postgres_url: str):
    """Test connectivity to both databases."""
    logger.info("Testing database connections...")

    # Test SQLite
    try:
        sqlite_engine = create_engine(sqlite_url)
        with sqlite_engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("✓ SQLite connection successful")
    except Exception as e:
        logger.error(f"✗ SQLite connection failed: {e}")
        raise

    # Test PostgreSQL
    try:
        postgres_engine = create_engine(postgres_url)
        with postgres_engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("✓ PostgreSQL connection successful")
    except Exception as e:
        logger.error(f"✗ PostgreSQL connection failed: {e}")
        raise

    return sqlite_engine, postgres_engine


def get_row_count(engine, table_name: str) -> int:
    """Get row count for a table."""
    try:
        with engine.connect() as conn:
            result = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            return result.scalar()
    except Exception:
        return 0


def migrate_table(sqlite_session, postgres_session, table_name: str, metadata: MetaData):
    """Migrate a single table from SQLite to PostgreSQL."""
    logger.info(f"Migrating table: {table_name}")

    try:
        # Get table definition
        table = Table(table_name, metadata, autoload_with=sqlite_session.bind)

        # Query all rows from SQLite
        rows = sqlite_session.execute(table.select()).fetchall()

        if not rows:
            logger.info(f"  ↳ No data to migrate")
            return 0

        # Insert rows into PostgreSQL in batches
        batch_size = 100
        total_rows = len(rows)
        migrated = 0

        for i in range(0, total_rows, batch_size):
            batch = rows[i:i + batch_size]

            try:
                # Convert rows to dictionaries
                batch_dicts = [dict(row._mapping) for row in batch]

                # Insert batch
                postgres_session.execute(table.insert(), batch_dicts)
                postgres_session.commit()

                migrated += len(batch)
                logger.info(f"  ↳ Migrated {migrated}/{total_rows} rows")

            except IntegrityError as e:
                logger.warning(f"  ↳ Integrity error in batch, trying row by row: {e}")
                postgres_session.rollback()

                # Try inserting rows one by one
                for row in batch:
                    try:
                        row_dict = dict(row._mapping)
                        postgres_session.execute(table.insert(), [row_dict])
                        postgres_session.commit()
                        migrated += 1
                    except IntegrityError as e:
                        logger.warning(f"  ↳ Skipping duplicate row: {e}")
                        postgres_session.rollback()
                        continue

        logger.info(f"  ✓ Migrated {migrated} rows")
        return migrated

    except Exception as e:
        logger.error(f"  ✗ Error migrating table {table_name}: {e}")
        postgres_session.rollback()
        raise


def reset_sequences(postgres_engine, table_names):
    """Reset PostgreSQL sequences after data import."""
    logger.info("Resetting PostgreSQL sequences...")

    with postgres_engine.connect() as conn:
        for table_name in table_names:
            try:
                # Get the max ID from the table
                result = conn.execute(f"SELECT MAX(id) FROM {table_name}")
                max_id = result.scalar()

                if max_id:
                    # Reset the sequence
                    sequence_name = f"{table_name}_id_seq"
                    conn.execute(f"SELECT setval('{sequence_name}', {max_id})")
                    logger.info(f"  ↳ Reset sequence for {table_name} to {max_id}")

            except Exception as e:
                logger.warning(f"  ↳ Could not reset sequence for {table_name}: {e}")
                continue

        conn.commit()


def verify_migration(sqlite_engine, postgres_engine, table_names):
    """Verify that all data was migrated correctly."""
    logger.info("\nVerifying migration...")

    all_match = True
    verification_results = []

    for table_name in table_names:
        sqlite_count = get_row_count(sqlite_engine, table_name)
        postgres_count = get_row_count(postgres_engine, table_name)

        match = sqlite_count == postgres_count
        symbol = "✓" if match else "✗"

        result = {
            'table': table_name,
            'sqlite_rows': sqlite_count,
            'postgres_rows': postgres_count,
            'match': match
        }
        verification_results.append(result)

        logger.info(f"  {symbol} {table_name}: SQLite={sqlite_count}, PostgreSQL={postgres_count}")

        if not match:
            all_match = False

    return all_match, verification_results


def main():
    parser = argparse.ArgumentParser(
        description='Migrate HomeRack database from SQLite to PostgreSQL'
    )
    parser.add_argument(
        '--sqlite-path',
        default='./homerack.db',
        help='Path to SQLite database file (default: ./homerack.db)'
    )
    parser.add_argument(
        '--postgres-url',
        required=True,
        help='PostgreSQL connection URL (e.g., postgresql://user:pass@host/db)'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip creating SQLite backup'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test connections and show migration plan without migrating'
    )

    args = parser.parse_args()

    # Validate SQLite path
    if not os.path.exists(args.sqlite_path):
        logger.error(f"SQLite database not found: {args.sqlite_path}")
        sys.exit(1)

    # Create backup unless --no-backup specified
    if not args.no_backup and not args.dry_run:
        backup_path = backup_sqlite_database(args.sqlite_path)
        logger.info(f"Backup created: {backup_path}")

    # Create connection URLs
    sqlite_url = f"sqlite:///{args.sqlite_path}"
    postgres_url = args.postgres_url

    # Test connections
    try:
        sqlite_engine, postgres_engine = test_database_connections(sqlite_url, postgres_url)
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        sys.exit(1)

    # Get table order
    table_order = get_table_order()

    # Show migration plan
    logger.info("\nMigration plan:")
    logger.info(f"  Source: {sqlite_url}")
    logger.info(f"  Target: {postgres_url}")
    logger.info(f"  Tables to migrate: {len(table_order)}")

    for i, table_name in enumerate(table_order, 1):
        row_count = get_row_count(sqlite_engine, table_name)
        logger.info(f"  {i}. {table_name} ({row_count} rows)")

    if args.dry_run:
        logger.info("\nDry run complete. No data was migrated.")
        sys.exit(0)

    # Confirm migration
    logger.info("\nReady to migrate. This will:")
    logger.info("  1. Migrate all data from SQLite to PostgreSQL")
    logger.info("  2. Preserve all relationships and constraints")
    logger.info("  3. Reset PostgreSQL sequences")
    logger.info("  4. Verify data integrity")

    response = input("\nProceed with migration? (yes/no): ")
    if response.lower() != 'yes':
        logger.info("Migration cancelled")
        sys.exit(0)

    # Create sessions
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    PostgresSession = sessionmaker(bind=postgres_engine)

    sqlite_session = SQLiteSession()
    postgres_session = PostgresSession()

    # Load metadata from SQLite
    metadata = MetaData()
    metadata.reflect(bind=sqlite_engine)

    # Migrate tables
    logger.info("\nStarting migration...")
    start_time = datetime.now()
    total_rows = 0

    try:
        for table_name in table_order:
            if table_name in metadata.tables:
                rows_migrated = migrate_table(sqlite_session, postgres_session, table_name, metadata)
                total_rows += rows_migrated
            else:
                logger.warning(f"  ↳ Table {table_name} not found in SQLite database")

        # Reset sequences
        reset_sequences(postgres_engine, table_order)

        # Verify migration
        all_match, results = verify_migration(sqlite_engine, postgres_engine, table_order)

        duration = (datetime.now() - start_time).total_seconds()

        logger.info(f"\n{'='*60}")
        logger.info(f"Migration completed in {duration:.2f} seconds")
        logger.info(f"Total rows migrated: {total_rows}")

        if all_match:
            logger.info("✓ All data verified successfully!")
        else:
            logger.warning("✗ Some tables have mismatched row counts")
            logger.warning("Please review the verification results above")

    except Exception as e:
        logger.error(f"\n✗ Migration failed: {e}")
        logger.error("Database may be in an inconsistent state")
        logger.error("You can restore from backup if needed")
        sys.exit(1)

    finally:
        sqlite_session.close()
        postgres_session.close()


if __name__ == '__main__':
    main()
