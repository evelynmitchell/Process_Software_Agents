"""
Initial database schema migration for Hello World API

Creates the foundational database tables for users and tasks with proper
indexes, constraints, and relationships.

Revision ID: 001
Revises: 
Create Date: 2025-11-21 03:48:25.246374

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
    
    This migration creates:
    - users table with authentication and profile information
    - tasks table with task management functionality
    - Proper indexes for query performance
    - Foreign key constraints for data integrity
    - Check constraints for data validation
    """
    # Create users table
    op.create_table(
        'users',
        sa.Column(
            'id',
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
            nullable=False,
            comment='Primary key for users table'
        ),
        sa.Column(
            'email',
            sa.String(255),
            nullable=False,
            comment='User email address, must be unique'
        ),
        sa.Column(
            'username',
            sa.String(50),
            nullable=False,
            comment='User display name, must be unique'
        ),
        sa.Column(
            'password_hash',
            sa.String(255),
            nullable=False,
            comment='Bcrypt hashed password'
        ),
        sa.Column(
            'first_name',
            sa.String(100),
            nullable=True,
            comment='User first name'
        ),
        sa.Column(
            'last_name',
            sa.String(100),
            nullable=True,
            comment='User last name'
        ),
        sa.Column(
            'is_active',
            sa.Boolean(),
            nullable=False,
            default=True,
            comment='Whether user account is active'
        ),
        sa.Column(
            'is_verified',
            sa.Boolean(),
            nullable=False,
            default=False,
            comment='Whether user email is verified'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
            comment='Timestamp when user was created'
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
            comment='Timestamp when user was last updated'
        ),
        sa.Column(
            'last_login_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Timestamp of last successful login'
        ),
        comment='User accounts and authentication information'
    )

    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column(
            'id',
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
            nullable=False,
            comment='Primary key for tasks table'
        ),
        sa.Column(
            'user_id',
            sa.Integer(),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
            comment='Foreign key reference to users table'
        ),
        sa.Column(
            'title',
            sa.String(200),
            nullable=False,
            comment='Task title or summary'
        ),
        sa.Column(
            'description',
            sa.Text(),
            nullable=True,
            comment='Detailed task description'
        ),
        sa.Column(
            'status',
            sa.Enum('pending', 'in_progress', 'completed', 'cancelled', name='task_status'),
            nullable=False,
            default='pending',
            comment='Current status of the task'
        ),
        sa.Column(
            'priority',
            sa.Enum('low', 'medium', 'high', 'urgent', name='task_priority'),
            nullable=False,
            default='medium',
            comment='Task priority level'
        ),
        sa.Column(
            'due_date',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Optional due date for task completion'
        ),
        sa.Column(
            'completed_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Timestamp when task was marked as completed'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
            comment='Timestamp when task was created'
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
            comment='Timestamp when task was last updated'
        ),
        comment='User tasks and todo items'
    )

    # Create unique constraints
    op.create_unique_constraint('uq_users_email', 'users', ['email'])
    op.create_unique_constraint('uq_users_username', 'users', ['username'])

    # Create indexes for performance optimization
    
    # Users table indexes
    op.create_index(
        'ix_users_email',
        'users',
        ['email'],
        unique=True,
        postgresql_using='btree'
    )
    op.create_index(
        'ix_users_username',
        'users',
        ['username'],
        unique=True,
        postgresql_using='btree'
    )
    op.create_index(
        'ix_users_is_active',
        'users',
        ['is_active'],
        postgresql_using='btree'
    )
    op.create_index(
        'ix_users_created_at',
        'users',
        ['created_at'],
        postgresql_using='btree'
    )
    op.create_index(
        'ix_users_last_login_at',
        'users',
        ['last_login_at'],
        postgresql_using='btree'
    )

    # Tasks table indexes
    op.create_index(
        'ix_tasks_user_id',
        'tasks',
        ['user_id'],
        postgresql_using='btree'
    )
    op.create_index(
        'ix_tasks_status',
        'tasks',
        ['status'],
        postgresql_using='btree'
    )
    op.create_index(
        'ix_tasks_priority',
        'tasks',
        ['priority'],
        postgresql_using='btree'
    )
    op.create_index(
        'ix_tasks_due_date',
        'tasks',
        ['due_date'],
        postgresql_using='btree'
    )
    op.create_index(
        'ix_tasks_created_at',
        'tasks',
        ['created_at'],
        postgresql_using='btree'
    )
    op.create_index(
        'ix_tasks_completed_at',
        'tasks',
        ['completed_at'],
        postgresql_using='btree'
    )

    # Composite indexes for common query patterns
    op.create_index(
        'ix_tasks_user_status',
        'tasks',
        ['user_id', 'status'],
        postgresql_using='btree'
    )
    op.create_index(
        'ix_tasks_user_priority',
        'tasks',
        ['user_id', 'priority'],
        postgresql_using='btree'
    )