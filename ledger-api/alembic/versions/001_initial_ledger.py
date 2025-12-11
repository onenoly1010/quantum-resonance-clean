"""Initial ledger schema

Revision ID: 001
Revises: 
Create Date: 2025-12-11

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import os

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply the initial ledger schema by executing the SQL file."""
    # Get the path to the SQL file
    sql_file_path = os.path.join(
        os.path.dirname(__file__), 
        '..', '..', 
        'sql', 'schema', 
        '001_initial_ledger.sql'
    )
    
    # Read and execute the SQL file
    with open(sql_file_path, 'r') as f:
        sql_content = f.read()
    
    # Execute the SQL
    op.execute(sql_content)


def downgrade() -> None:
    """Rollback the initial schema."""
    op.drop_table('reconciliation_log')
    op.drop_table('audit_log')
    op.drop_table('allocation_rules')
    op.drop_table('ledger_transactions')
    op.drop_table('logical_accounts')
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE')
