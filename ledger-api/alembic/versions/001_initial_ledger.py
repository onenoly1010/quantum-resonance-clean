"""Initial ledger schema

Revision ID: 001_initial_ledger
Revises: 
Create Date: 2025-12-11 02:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from pathlib import Path

# revision identifiers, used by Alembic.
revision: str = '001_initial_ledger'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply initial ledger schema from SQL file"""
    # Read and execute the SQL schema file
    sql_file_path = Path(__file__).parent.parent.parent / "sql" / "schema" / "001_initial_ledger.sql"
    
    with open(sql_file_path, 'r') as f:
        sql_content = f.read()
    
    # Execute the SQL file content
    # Split on semicolons but be careful with comments and strings
    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
    
    for statement in statements:
        if statement and not statement.startswith('--'):
            op.execute(statement)


def downgrade() -> None:
    """Remove all tables and extensions created in upgrade"""
    # Drop views first
    op.execute("DROP VIEW IF EXISTS account_summary CASCADE")
    
    # Drop tables in reverse order of dependencies
    op.execute("DROP TABLE IF EXISTS reconciliation_log CASCADE")
    op.execute("DROP TABLE IF EXISTS audit_log CASCADE")
    op.execute("DROP TABLE IF EXISTS allocation_rules CASCADE")
    op.execute("DROP TABLE IF EXISTS ledger_transactions CASCADE")
    op.execute("DROP TABLE IF EXISTS logical_accounts CASCADE")
    
    # Drop trigger function
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE")
    
    # Note: We don't drop the uuid-ossp extension as other schemas might use it
