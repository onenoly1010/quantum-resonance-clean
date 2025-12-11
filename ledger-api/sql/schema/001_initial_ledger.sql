-- Ledger API Initial Schema Migration
-- Version: 001
-- Description: Creates core ledger tables for transactions, accounts, allocations, audit, and reconciliation

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Logical Accounts Table
-- Represents abstract account categories (e.g., Revenue, Operations, Treasury)
CREATE TABLE logical_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL CHECK (type IN ('ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE')),
    metadata JSONB DEFAULT '{}',
    balance NUMERIC(30, 12) DEFAULT 0 NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Create index on account type for faster queries
CREATE INDEX idx_logical_accounts_type ON logical_accounts(type);
CREATE INDEX idx_logical_accounts_balance ON logical_accounts(balance);

-- Ledger Transactions Table
-- Records all financial transactions in the system
CREATE TABLE ledger_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('DEPOSIT', 'WITHDRAWAL', 'TRANSFER', 'ALLOCATION', 'CORRECTION')),
    amount NUMERIC(30, 12) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'COMPLETED', 'FAILED', 'CANCELLED')),
    metadata JSONB DEFAULT '{}',
    external_tx_hash TEXT,
    logical_account_id UUID REFERENCES logical_accounts(id) ON DELETE RESTRICT,
    parent_transaction_id UUID REFERENCES ledger_transactions(id) ON DELETE SET NULL,
    description TEXT
);

-- Create indexes for common queries
CREATE INDEX idx_ledger_transactions_account ON ledger_transactions(logical_account_id);
CREATE INDEX idx_ledger_transactions_status ON ledger_transactions(status);
CREATE INDEX idx_ledger_transactions_type ON ledger_transactions(type);
CREATE INDEX idx_ledger_transactions_created_at ON ledger_transactions(created_at DESC);
CREATE INDEX idx_ledger_transactions_external_hash ON ledger_transactions(external_tx_hash) WHERE external_tx_hash IS NOT NULL;
CREATE INDEX idx_ledger_transactions_parent ON ledger_transactions(parent_transaction_id) WHERE parent_transaction_id IS NOT NULL;

-- Allocation Rules Table
-- Defines how transactions should be split across accounts
CREATE TABLE allocation_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    rules JSONB NOT NULL,
    active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    created_by TEXT,
    description TEXT
);

-- Create index for active rules
CREATE INDEX idx_allocation_rules_active ON allocation_rules(active) WHERE active = true;

-- Audit Log Table
-- Comprehensive audit trail for all operations
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action TEXT NOT NULL,
    actor TEXT NOT NULL,
    target_id UUID,
    target_type TEXT,
    details JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    ip_address TEXT,
    user_agent TEXT
);

-- Create indexes for audit queries
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at DESC);
CREATE INDEX idx_audit_log_actor ON audit_log(actor);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_target ON audit_log(target_id, target_type);

-- Reconciliation Log Table
-- Tracks external vs internal balance reconciliation
CREATE TABLE reconciliation_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    logical_account_id UUID NOT NULL REFERENCES logical_accounts(id) ON DELETE RESTRICT,
    external_balance NUMERIC(30, 12) NOT NULL,
    internal_balance NUMERIC(30, 12) NOT NULL,
    discrepancy NUMERIC(30, 12) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    resolved BOOLEAN DEFAULT false NOT NULL,
    resolved_at TIMESTAMPTZ,
    resolved_by TEXT,
    resolution_notes TEXT,
    correction_transaction_id UUID REFERENCES ledger_transactions(id) ON DELETE SET NULL
);

-- Create indexes for reconciliation queries
CREATE INDEX idx_reconciliation_log_account ON reconciliation_log(logical_account_id);
CREATE INDEX idx_reconciliation_log_created_at ON reconciliation_log(created_at DESC);
CREATE INDEX idx_reconciliation_log_resolved ON reconciliation_log(resolved);

-- Create trigger function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_logical_accounts_updated_at
    BEFORE UPDATE ON logical_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ledger_transactions_updated_at
    BEFORE UPDATE ON ledger_transactions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_allocation_rules_updated_at
    BEFORE UPDATE ON allocation_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create view for account balances with transaction counts
CREATE VIEW account_summary AS
SELECT 
    la.id,
    la.name,
    la.type,
    la.balance,
    la.metadata,
    COUNT(lt.id) as transaction_count,
    MAX(lt.created_at) as last_transaction_at
FROM logical_accounts la
LEFT JOIN ledger_transactions lt ON la.id = lt.logical_account_id
GROUP BY la.id, la.name, la.type, la.balance, la.metadata;

-- Insert default system accounts
INSERT INTO logical_accounts (name, type, metadata) VALUES
    ('Treasury', 'ASSET', '{"description": "Main treasury account"}'),
    ('Operations', 'EXPENSE', '{"description": "Operational expenses"}'),
    ('Development', 'EXPENSE', '{"description": "Development expenses"}'),
    ('Reserve', 'ASSET', '{"description": "Reserve fund"}'),
    ('Revenue', 'REVENUE', '{"description": "Primary revenue account"}');

-- Add comments for documentation
COMMENT ON TABLE logical_accounts IS 'Abstract account categories for transaction organization';
COMMENT ON TABLE ledger_transactions IS 'All financial transactions with full audit trail';
COMMENT ON TABLE allocation_rules IS 'Rules for automatic transaction splitting';
COMMENT ON TABLE audit_log IS 'Comprehensive audit log for compliance';
COMMENT ON TABLE reconciliation_log IS 'External balance reconciliation tracking';

COMMENT ON COLUMN ledger_transactions.parent_transaction_id IS 'References parent transaction for allocations';
COMMENT ON COLUMN allocation_rules.rules IS 'JSONB array of {destination_account_id, percentage, description}';
COMMENT ON COLUMN reconciliation_log.discrepancy IS 'Calculated as external_balance - internal_balance';
