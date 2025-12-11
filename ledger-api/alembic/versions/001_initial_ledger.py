"""Initial ledger schema

Revision ID: 001_initial
Revises: 
Create Date: 2025-12-11 02:36:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from pathlib import Path


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Read and execute the SQL schema file
    sql_file = Path(__file__).parent.parent.parent / "sql" / "schema" / "001_initial_ledger.sql"
    with open(sql_file, 'r') as f:
        sql_content = f.read()
    
    # Execute the SQL statements
    for statement in sql_content.split(';'):
        statement = statement.strip()
        if statement:
            op.execute(statement)


def downgrade() -> None:
    # Drop all tables in reverse order
    op.execute("DROP TABLE IF EXISTS reconciliation_log CASCADE")
    op.execute("DROP TABLE IF EXISTS audit_log CASCADE")
    op.execute("DROP TABLE IF EXISTS allocation_rules CASCADE")
    op.execute("DROP TABLE IF EXISTS ledger_transactions CASCADE")
    op.execute("DROP TABLE IF EXISTS logical_accounts CASCADE")
    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
    op.execute("DROP EXTENSION IF EXISTS \"uuid-ossp\"")
