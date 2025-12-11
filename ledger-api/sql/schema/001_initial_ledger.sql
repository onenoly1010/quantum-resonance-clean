-- 001_initial_ledger.sql
-- Creates the core ledger database schema

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Logical accounts table
CREATE TABLE IF NOT EXISTS logical_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    account_type VARCHAR(50) NOT NULL,
    balance NUMERIC(30, 12) NOT NULL DEFAULT 0,
    currency VARCHAR(10) NOT NULL DEFAULT 'PI',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Ledger transactions table
CREATE TABLE IF NOT EXISTS ledger_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_type VARCHAR(50) NOT NULL,
    amount NUMERIC(30, 12) NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'PI',
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    logical_account_id UUID REFERENCES logical_accounts(id),
    parent_transaction_id UUID REFERENCES ledger_transactions(id),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Allocation rules table
CREATE TABLE IF NOT EXISTS allocation_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    rule_data JSONB NOT NULL,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action VARCHAR(100) NOT NULL,
    actor VARCHAR(255) NOT NULL,
    target_id UUID,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Reconciliation log table
CREATE TABLE IF NOT EXISTS reconciliation_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    logical_account_id UUID REFERENCES logical_accounts(id) NOT NULL,
    ledger_balance NUMERIC(30, 12) NOT NULL,
    external_balance NUMERIC(30, 12) NOT NULL,
    discrepancy NUMERIC(30, 12) NOT NULL,
    reconciled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_ledger_tx_account ON ledger_transactions(logical_account_id);
CREATE INDEX IF NOT EXISTS idx_ledger_tx_parent ON ledger_transactions(parent_transaction_id);
CREATE INDEX IF NOT EXISTS idx_ledger_tx_type ON ledger_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_ledger_tx_status ON ledger_transactions(status);
CREATE INDEX IF NOT EXISTS idx_audit_log_actor ON audit_log(actor);
CREATE INDEX IF NOT EXISTS idx_audit_log_target ON audit_log(target_id);
CREATE INDEX IF NOT EXISTS idx_reconciliation_account ON reconciliation_log(logical_account_id);
