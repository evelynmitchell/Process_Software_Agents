"""
Initial database schema migration for Hello World API

Creates the initial database tables, indexes, and constraints.
This is a placeholder migration as the Hello World API doesn't require a database.

Revision ID: 001
Revises: 
Create Date: 2025-11-21 02:21:40.723332

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
    Note: The Hello World API is stateless and doesn't require database tables,
    but this migration is included for completeness and future extensibility.
    
    Tables created:
    - api_metadata: Stores API version and configuration metadata
    - request_logs: Optional table for request logging (disabled by default)
    """
    # Create api_metadata table for storing API configuration
    op.create_table(
        'api_metadata',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('key', sa.String(100), nullable=False, unique=True),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, 
                 server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                 server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key', name='uq_api_metadata_key')
    )
    
    # Create index on key column for fast lookups
    op.create_index(
        'ix_api_metadata_key',
        'api_metadata',
        ['key'],
        unique=True
    )
    
    # Create index on created_at for time-based queries
    op.create_index(
        'ix_api_metadata_created_at',
        'api_metadata',
        ['created_at']
    )
    
    # Create request_logs table for optional request logging
    # This table is not used by the current Hello World API but provides
    # foundation for future logging requirements
    op.create_table(
        'request_logs',
        sa.Column('id', sa.BigInteger(), nullable=False, primary_key=True),
        sa.Column('request_id', sa.String(36), nullable=False, unique=True),
        sa.Column('method', sa.String(10), nullable=False),
        sa.Column('path', sa.String(255), nullable=False),
        sa.Column('query_params', sa.Text(), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),  # IPv6 compatible
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('error_code', sa.String(50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                 server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('request_id', name='uq_request_logs_request_id')
    )
    
    # Create indexes for request_logs table
    op.create_index(
        'ix_request_logs_request_id',
        'request_logs',
        ['request_id'],
        unique=True
    )
    
    op.create_index(
        'ix_request_logs_created_at',
        'request_logs',
        ['created_at']
    )
    
    op.create_index(
        'ix_request_logs_method_path',
        'request_logs',
        ['method', 'path']
    )
    
    op.create_index(
        'ix_request_logs_status_code',
        'request_logs',
        ['status_code']
    )
    
    op.create_index(
        'ix_request_logs_ip_address',
        'request_logs',
        ['ip_address']
    )
    
    # Insert initial API metadata
    op.execute(
        sa.text("""
        INSERT INTO api_metadata (key, value, description) VALUES
        ('api_version', '1.0.0', 'Current API version'),
        ('api_title', 'Hello World API', 'API title'),
        ('api_description', 'Simple REST API that returns greeting messages', 'API description'),
        ('schema_version', '001', 'Current database schema version'),
        ('created_date', :created_date, 'Date when API was first deployed'),
        ('logging_enabled', 'false', 'Whether request logging is enabled'),
        ('max_name_length', '100', 'Maximum allowed length for name parameter'),
        ('allowed_name_pattern', '^[a-zA-Z0-9\\s]*$', 'Regex pattern for valid name characters')
        """),
        created_date='2025-11-21T02:21:40.723332Z'
    )


def downgrade() -> None:
    """
    Downgrade database schema from revision 001.
    
    Drops all tables and indexes created in the upgrade() function.
    This will permanently delete all data in these tables.
    """
    # Drop indexes first (foreign key constraints would be dropped here if they existed)
    op.drop_index('ix_request_logs_ip_address', table_name='request_logs')
    op.drop_index('ix_request_logs_status_code', table_name='request_logs')
    op.drop_index('ix_request_logs_method_path', table_name='request_logs')
    op.drop_index('ix_request_logs_created_at', table_name='request_logs')
    op.drop_index('ix_request_logs_request_id', table_name='request_logs')
    
    op.drop_index('ix_api_metadata_created_at', table_name='api_metadata')
    op.drop_index('ix_api_metadata_key', table_name='api_metadata')
    
    # Drop tables
    op.drop_table('request_logs')
    op.drop_table('api_metadata')


def get_current_schema_version() -> str:
    """
    Get the current schema version from this migration.
    
    Returns:
        str: The revision identifier for this migration
        
    Note:
        This is a utility function that can be used by the application
        to verify the current database schema version.
    """
    return revision


def validate_schema_compatibility() -> bool:
    """
    Validate that the current schema is compatible with the API requirements.
    
    Returns:
        bool: True if schema is compatible, False otherwise
        
    Note:
        This function can be extended to perform more complex validation
        as the API evolves and requires additional database features.
    """
    # For the Hello World API, any schema version is compatible
    # since the API doesn't actually use the database tables
    return True


def get_migration_description() -> str:
    """
    Get a human-readable description of what this migration does.
    
    Returns:
        str: Description of the migration changes
    """
    return (
        "Initial schema migration for Hello World API. "
        "Creates api_metadata table for configuration storage and "
        "request_