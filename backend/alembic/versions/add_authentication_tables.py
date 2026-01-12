"""Add authentication tables

Revision ID: auth_001
Revises: 2785cd8e7011
Create Date: 2026-01-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'auth_001'
down_revision = '2785cd8e7011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create authentication tables."""

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('role', sa.Enum('ADMIN', 'USER', 'READONLY', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for users table
    op.create_index('ix_users_id', 'users', ['id'], unique=False)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_role', 'users', ['role'], unique=False)
    op.create_index('ix_users_email_active', 'users', ['email', 'is_active'], unique=False)

    # Create token_blacklist table
    op.create_table(
        'token_blacklist',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token_jti', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for token_blacklist table
    op.create_index('ix_token_blacklist_id', 'token_blacklist', ['id'], unique=False)
    op.create_index('ix_token_blacklist_token_jti', 'token_blacklist', ['token_jti'], unique=True)
    op.create_index('ix_token_blacklist_expires', 'token_blacklist', ['expires_at'], unique=False)

    # Insert default admin user (password: Admin123!)
    # Password hash for "Admin123!" - CHANGE THIS IN PRODUCTION
    op.execute(
        """
        INSERT INTO users (email, hashed_password, full_name, role, is_active, created_at, updated_at)
        VALUES (
            'admin@homerack.local',
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LwKW5L5qm5wJ5OUoW',
            'System Administrator',
            'ADMIN',
            TRUE,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        )
        """
    )


def downgrade() -> None:
    """Drop authentication tables."""
    op.drop_index('ix_token_blacklist_expires', table_name='token_blacklist')
    op.drop_index('ix_token_blacklist_token_jti', table_name='token_blacklist')
    op.drop_index('ix_token_blacklist_id', table_name='token_blacklist')
    op.drop_table('token_blacklist')

    op.drop_index('ix_users_email_active', table_name='users')
    op.drop_index('ix_users_role', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_id', table_name='users')
    op.drop_table('users')

    # Drop the enum type if using PostgreSQL
    # For SQLite, this is not needed as it doesn't have native enum types
    # op.execute('DROP TYPE IF EXISTS userrole')
