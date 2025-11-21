"""
Initial database schema migration for Hello World API

Creates the foundational database tables for user management and task tracking
with proper indexes, constraints, and relationships.

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

Component ID: COMP-011
Semantic Unit: SU-011

Author: ASP Code Agent
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create initial database schema with users and tasks tables.
    
    Creates:
    - users table with authentication and profile fields
    - tasks table with task management fields
    - Indexes for performance optimization
    - Foreign key constraints for data integrity
    """
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, 
                 server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                 server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    
    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, default='pending'),
        sa.Column('priority', sa.String(length=10), nullable=False, default='medium'),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                 server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                 server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    
    # Create indexes for performance optimization
    
    # Users table indexes
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_username', 'users', ['username'])
    op.create_index('idx_users_is_active', 'users', ['is_active'])
    op.create_index('idx_users_created_at', 'users', ['created_at'])
    
    # Tasks table indexes
    op.create_index('idx_tasks_user_id', 'tasks', ['user_id'])
    op.create_index('idx_tasks_status', 'tasks', ['status'])
    op.create_index('idx_tasks_priority', 'tasks', ['priority'])
    op.create_index('idx_tasks_due_date', 'tasks', ['due_date'])
    op.create_index('idx_tasks_created_at', 'tasks', ['created_at'])
    op.create_index('idx_tasks_user_status', 'tasks', ['user_id', 'status'])
    op.create_index('idx_tasks_user_priority', 'tasks', ['user_id', 'priority'])
    
    # Add check constraints for data validation
    op.create_check_constraint(
        'ck_users_email_format',
        'users',
        sa.text("email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'")
    )
    
    op.create_check_constraint(
        'ck_users_username_length',
        'users',
        sa.text("length(username) >= 3")
    )
    
    op.create_check_constraint(
        'ck_tasks_status_valid',
        'tasks',
        sa.text("status IN ('pending', 'in_progress', 'completed', 'cancelled')")
    )
    
    op.create_check_constraint(
        'ck_tasks_priority_valid',
        'tasks',
        sa.text("priority IN ('low', 'medium', 'high', 'urgent')")
    )
    
    op.create_check_constraint(
        'ck_tasks_title_length',
        'tasks',
        sa.text("length(trim(title)) > 0")
    )


def downgrade() -> None:
    """
    Drop all tables and indexes created in upgrade.
    
    Removes:
    - All indexes
    - tasks table (with foreign key constraints)
    - users table
    """
    # Drop indexes first
    op.drop_index('idx_tasks_user_priority', table_name='tasks')
    op.drop_index('idx_tasks_user_status', table_name='tasks')
    op.drop_index('idx_tasks_created_at', table_name='tasks')
    op.drop_index('idx_tasks_due_date', table_name='tasks')
    op.drop_index('idx_tasks_priority', table_name='tasks')
    op.drop_index('idx_tasks_status', table_name='tasks')
    op.drop_index('idx_tasks_user_id', table_name='tasks')
    
    op.drop_index('idx_users_created_at', table_name='users')
    op.drop_index('idx_users_is_active', table_name='users')
    op.drop_index('idx_users_username', table_name='users')
    op.drop_index('idx_users_email', table_name='users')
    
    # Drop tables (tasks first due to foreign key dependency)
    op.drop_table('tasks')
    op.drop_table('users')