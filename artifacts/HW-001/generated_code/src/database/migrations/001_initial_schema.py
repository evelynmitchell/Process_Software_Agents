"""
Initial database schema migration for Hello World API

Creates the foundational database tables, indexes, and constraints.
This is a placeholder migration as the Hello World API doesn't require a database.

Revision ID: 001
Revises: 
Create Date: 2025-11-21 17:46:28.707525

Component ID: COMP-011
Semantic Unit: SU-011

Author: ASP Code Agent
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade database schema to revision 001.
    
    Creates initial database tables for the Hello World API.
    Note: The Hello World API doesn't actually require database tables,
    but this migration serves as a template for future schema changes.
    """
    # Create users table for potential future authentication
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    
    # Create index on username for faster lookups
    op.create_index('idx_users_username', 'users', ['username'])
    
    # Create index on email for faster lookups
    op.create_index('idx_users_email', 'users', ['email'])
    
    # Create index on created_at for chronological queries
    op.create_index('idx_users_created_at', 'users', ['created_at'])
    
    # Create tasks table for potential future task management
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, default='pending'),
        sa.Column('priority', sa.String(length=10), nullable=False, default='medium'),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.CheckConstraint("status IN ('pending', 'in_progress', 'completed', 'cancelled')", name='check_task_status'),
        sa.CheckConstraint("priority IN ('low', 'medium', 'high', 'urgent')", name='check_task_priority')
    )
    
    # Create index on user_id for faster user task lookups
    op.create_index('idx_tasks_user_id', 'tasks', ['user_id'])
    
    # Create index on status for filtering tasks by status
    op.create_index('idx_tasks_status', 'tasks', ['status'])
    
    # Create index on priority for filtering tasks by priority
    op.create_index('idx_tasks_priority', 'tasks', ['priority'])
    
    # Create index on due_date for chronological queries
    op.create_index('idx_tasks_due_date', 'tasks', ['due_date'])
    
    # Create composite index on user_id and status for common queries
    op.create_index('idx_tasks_user_status', 'tasks', ['user_id', 'status'])
    
    # Create composite index on user_id and created_at for user task history
    op.create_index('idx_tasks_user_created', 'tasks', ['user_id', 'created_at'])


def downgrade() -> None:
    """
    Downgrade database schema from revision 001.
    
    Drops all tables and indexes created in the upgrade function.
    This will permanently delete all data in these tables.
    """
    # Drop indexes first (foreign key indexes are dropped automatically)
    op.drop_index('idx_tasks_user_created', table_name='tasks')
    op.drop_index('idx_tasks_user_status', table_name='tasks')
    op.drop_index('idx_tasks_due_date', table_name='tasks')
    op.drop_index('idx_tasks_priority', table_name='tasks')
    op.drop_index('idx_tasks_status', table_name='tasks')
    op.drop_index('idx_tasks_user_id', table_name='tasks')
    
    # Drop tasks table (foreign key constraints are dropped automatically)
    op.drop_table('tasks')
    
    # Drop user indexes
    op.drop_index('idx_users_created_at', table_name='users')
    op.drop_index('idx_users_email', table_name='users')
    op.drop_index('idx_users_username', table_name='users')
    
    # Drop users table
    op.drop_table('users')