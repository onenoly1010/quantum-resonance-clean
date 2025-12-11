"""Initial ledger schema

Revision ID: 001
Revises: 
Create Date: 2025-01-01 00:00:00.000000

This migration applies the initial ledger schema from SQL file.
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
    """Apply the initial schema from SQL file."""
    # Read and execute the SQL schema file
    sql_file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'sql', 'schema', '001_initial_ledger.sql'
    )
    
    # Note: In production, you might want to execute the SQL file directly
    # For now, we'll create tables using Alembic operations to match the schema
    
    # Create UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create logical_accounts table
    op.create_table(
        'logical_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('account_name', sa.String(255), nullable=False, unique=True),
        sa.Column('account_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("account_type IN ('asset', 'liability', 'equity', 'revenue', 'expense')")
    )
    
    # Create ledger_transactions table
    op.create_table(
        'ledger_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('transaction_date', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logical_accounts.id'), nullable=False),
        sa.Column('amount', sa.DECIMAL(20, 8), nullable=False),
        sa.Column('currency', sa.String(10), nullable=False, server_default='USD'),
        sa.Column('transaction_type', sa.String(50), nullable=False),
        sa.Column('reference_id', sa.String(255)),
        sa.Column('description', sa.Text),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("transaction_type IN ('debit', 'credit')")
    )
    
    # Create allocation_rules table
    op.create_table(
        'allocation_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('rule_name', sa.String(255), nullable=False, unique=True),
        sa.Column('source_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logical_accounts.id'), nullable=False),
        sa.Column('allocation_config', postgresql.JSONB, nullable=False),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('effective_from', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('effective_to', sa.TIMESTAMP(timezone=True)),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now())
    )
    
    # Create audit_log table
    op.create_table(
        'audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('user_id', sa.String(255)),
        sa.Column('changes', postgresql.JSONB),
        sa.Column('ip_address', postgresql.INET),
        sa.Column('user_agent', sa.Text),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("action IN ('create', 'update', 'delete', 'read')")
    )
    
    # Create reconciliation_log table
    op.create_table(
        'reconciliation_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('logical_accounts.id'), nullable=False),
        sa.Column('reconciliation_date', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('expected_balance', sa.DECIMAL(20, 8), nullable=False),
        sa.Column('actual_balance', sa.DECIMAL(20, 8), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('notes', sa.Text),
        sa.Column('reconciled_by', sa.String(255)),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('resolved_at', sa.TIMESTAMP(timezone=True)),
        sa.CheckConstraint("status IN ('pending', 'matched', 'variance', 'resolved')")
    )
    
    # Create indexes
    op.create_index('idx_ledger_transactions_account_id', 'ledger_transactions', ['account_id'])
    op.create_index('idx_ledger_transactions_transaction_date', 'ledger_transactions', ['transaction_date'])
    op.create_index('idx_ledger_transactions_reference_id', 'ledger_transactions', ['reference_id'])
    op.create_index('idx_allocation_rules_source_account_id', 'allocation_rules', ['source_account_id'])
    op.create_index('idx_allocation_rules_is_active', 'allocation_rules', ['is_active'])
    op.create_index('idx_audit_log_entity_type_id', 'audit_log', ['entity_type', 'entity_id'])
    op.create_index('idx_audit_log_timestamp', 'audit_log', ['timestamp'])
    op.create_index('idx_reconciliation_log_account_id', 'reconciliation_log', ['account_id'])
    op.create_index('idx_reconciliation_log_status', 'reconciliation_log', ['status'])
    
    # Create triggers for updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER update_logical_accounts_updated_at
        BEFORE UPDATE ON logical_accounts
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    
    op.execute("""
        CREATE TRIGGER update_ledger_transactions_updated_at
        BEFORE UPDATE ON ledger_transactions
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    
    op.execute("""
        CREATE TRIGGER update_allocation_rules_updated_at
        BEFORE UPDATE ON allocation_rules
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Remove all tables and extensions."""
    op.drop_table('reconciliation_log')
    op.drop_table('audit_log')
    op.drop_table('allocation_rules')
    op.drop_table('ledger_transactions')
    op.drop_table('logical_accounts')
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column()')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
