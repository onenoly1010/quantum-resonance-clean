"""Initial ledger schema migration

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the initial schema from SQL file."""
    # The actual schema is applied via the SQL file: sql/schema/001_initial_ledger.sql
    # This migration serves as a reference point for Alembic
    # In production, you would run the SQL file manually or use:
    # op.execute(open('sql/schema/001_initial_ledger.sql').read())
    pass


def downgrade() -> None:
    """Downgrade would drop all tables - use with caution."""
    # Drop all tables in reverse order of dependencies
    op.drop_table('audit_log')
    op.drop_table('reconciliations')
    op.drop_table('treasury_accounts')
    op.drop_table('allocation_rules')
    op.drop_table('transaction_lines')
    op.drop_table('transactions')
    op.drop_table('accounts')
    
    # Drop the extension
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
