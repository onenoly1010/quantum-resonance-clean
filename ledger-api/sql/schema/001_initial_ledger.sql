-- Ledger API Database Schema
-- This schema provides a single source of truth for ledger transactions, 
-- logical accounts, allocation rules, audit logs, and reconciliation logs.

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Logical Accounts Table
-- Stores all logical account definitions for the ledger system
CREATE TABLE logical_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_name VARCHAR(255) NOT NULL UNIQUE,
    account_type VARCHAR(50) NOT NULL CHECK (account_type IN ('asset', 'liability', 'equity', 'revenue', 'expense')),
    description TEXT,
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Ledger Transactions Table
-- Stores all financial transactions in the ledger
CREATE TABLE ledger_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    account_id UUID NOT NULL REFERENCES logical_accounts(id),
    amount DECIMAL(20, 8) NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    transaction_type VARCHAR(50) NOT NULL CHECK (transaction_type IN ('debit', 'credit')),
    reference_id VARCHAR(255),
    description TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Allocation Rules Table
-- Stores rules for automatic fund allocation across accounts
CREATE TABLE allocation_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_name VARCHAR(255) NOT NULL UNIQUE,
    source_account_id UUID NOT NULL REFERENCES logical_accounts(id),
    allocation_config JSONB NOT NULL,
    -- allocation_config format: [{"destination_account_id": "uuid", "percentage": 25.5, "priority": 1}]
    is_active BOOLEAN DEFAULT true,
    effective_from TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    effective_to TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Audit Log Table
-- Tracks all changes and actions in the ledger system
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL CHECK (action IN ('create', 'update', 'delete', 'read')),
    user_id VARCHAR(255),
    changes JSONB,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Reconciliation Log Table
-- Tracks reconciliation activities for accounts
CREATE TABLE reconciliation_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES logical_accounts(id),
    reconciliation_date TIMESTAMP WITH TIME ZONE NOT NULL,
    expected_balance DECIMAL(20, 8) NOT NULL,
    actual_balance DECIMAL(20, 8) NOT NULL,
    variance DECIMAL(20, 8) GENERATED ALWAYS AS (actual_balance - expected_balance) STORED,
    status VARCHAR(50) NOT NULL CHECK (status IN ('pending', 'matched', 'variance', 'resolved')),
    notes TEXT,
    reconciled_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for performance
CREATE INDEX idx_ledger_transactions_account_id ON ledger_transactions(account_id);
CREATE INDEX idx_ledger_transactions_transaction_date ON ledger_transactions(transaction_date);
CREATE INDEX idx_ledger_transactions_reference_id ON ledger_transactions(reference_id);
CREATE INDEX idx_allocation_rules_source_account_id ON allocation_rules(source_account_id);
CREATE INDEX idx_allocation_rules_is_active ON allocation_rules(is_active);
CREATE INDEX idx_audit_log_entity_type_id ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX idx_reconciliation_log_account_id ON reconciliation_log(account_id);
CREATE INDEX idx_reconciliation_log_status ON reconciliation_log(status);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers
CREATE TRIGGER update_logical_accounts_updated_at
    BEFORE UPDATE ON logical_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ledger_transactions_updated_at
    BEFORE UPDATE ON ledger_transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_allocation_rules_updated_at
    BEFORE UPDATE ON allocation_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust as needed for your environment)
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO ledger_api_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ledger_api_user;
