-- Ledger API Database Schema - Initial Setup
-- Version: 001
-- Description: Create core tables for ledger system

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Logical Accounts Table
-- Stores account definitions and metadata
CREATE TABLE IF NOT EXISTS logical_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_code VARCHAR(50) UNIQUE NOT NULL,
    account_name VARCHAR(255) NOT NULL,
    account_type VARCHAR(50) NOT NULL CHECK (account_type IN ('asset', 'liability', 'equity', 'revenue', 'expense')),
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'archived')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255)
);

-- Create indexes for logical_accounts
CREATE INDEX idx_logical_accounts_code ON logical_accounts(account_code);
CREATE INDEX idx_logical_accounts_type ON logical_accounts(account_type);
CREATE INDEX idx_logical_accounts_status ON logical_accounts(status);

-- Ledger Transactions Table
-- Stores all financial transactions using double-entry accounting
CREATE TABLE IF NOT EXISTS ledger_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_ref VARCHAR(100) UNIQUE NOT NULL,
    transaction_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description TEXT NOT NULL,
    debit_account_id UUID NOT NULL REFERENCES logical_accounts(id),
    credit_account_id UUID NOT NULL REFERENCES logical_accounts(id),
    amount NUMERIC(20, 2) NOT NULL CHECK (amount > 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'posted', 'reversed', 'cancelled')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    CONSTRAINT different_accounts CHECK (debit_account_id != credit_account_id)
);

-- Create indexes for ledger_transactions
CREATE INDEX idx_ledger_transactions_ref ON ledger_transactions(transaction_ref);
CREATE INDEX idx_ledger_transactions_date ON ledger_transactions(transaction_date);
CREATE INDEX idx_ledger_transactions_debit ON ledger_transactions(debit_account_id);
CREATE INDEX idx_ledger_transactions_credit ON ledger_transactions(credit_account_id);
CREATE INDEX idx_ledger_transactions_status ON ledger_transactions(status);

-- Allocation Rules Table
-- Stores rules for automated transaction allocation
CREATE TABLE IF NOT EXISTS allocation_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_name VARCHAR(255) UNIQUE NOT NULL,
    rule_description TEXT,
    source_account_id UUID NOT NULL REFERENCES logical_accounts(id),
    allocation_logic JSONB NOT NULL,
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    effective_from TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    effective_to TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255)
);

-- Create indexes for allocation_rules
CREATE INDEX idx_allocation_rules_source ON allocation_rules(source_account_id);
CREATE INDEX idx_allocation_rules_active ON allocation_rules(is_active);
CREATE INDEX idx_allocation_rules_priority ON allocation_rules(priority);

-- Audit Log Table
-- Immutable log of all operations for compliance and tracking
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID,
    changes JSONB,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB DEFAULT '{}'
);

-- Create indexes for audit_log
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_log_user ON audit_log(user_id);
CREATE INDEX idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);

-- Reconciliation Log Table
-- Tracks reconciliation operations
CREATE TABLE IF NOT EXISTS reconciliation_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reconciliation_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    account_id UUID NOT NULL REFERENCES logical_accounts(id),
    reconciliation_type VARCHAR(50) NOT NULL,
    expected_balance NUMERIC(20, 2) NOT NULL,
    actual_balance NUMERIC(20, 2) NOT NULL,
    difference NUMERIC(20, 2) GENERATED ALWAYS AS (actual_balance - expected_balance) STORED,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'matched', 'unmatched', 'reviewed')),
    notes TEXT,
    reconciled_by VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for reconciliation_log
CREATE INDEX idx_reconciliation_log_date ON reconciliation_log(reconciliation_date);
CREATE INDEX idx_reconciliation_log_account ON reconciliation_log(account_id);
CREATE INDEX idx_reconciliation_log_status ON reconciliation_log(status);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_logical_accounts_updated_at BEFORE UPDATE ON logical_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ledger_transactions_updated_at BEFORE UPDATE ON ledger_transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_allocation_rules_updated_at BEFORE UPDATE ON allocation_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reconciliation_log_updated_at BEFORE UPDATE ON reconciliation_log
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create a view for account balances
CREATE OR REPLACE VIEW account_balances AS
SELECT 
    la.id as account_id,
    la.account_code,
    la.account_name,
    la.account_type,
    COALESCE(SUM(CASE WHEN lt.debit_account_id = la.id AND lt.status = 'posted' THEN lt.amount ELSE 0 END), 0) as total_debits,
    COALESCE(SUM(CASE WHEN lt.credit_account_id = la.id AND lt.status = 'posted' THEN lt.amount ELSE 0 END), 0) as total_credits,
    COALESCE(SUM(CASE WHEN lt.debit_account_id = la.id AND lt.status = 'posted' THEN lt.amount ELSE 0 END), 0) - 
    COALESCE(SUM(CASE WHEN lt.credit_account_id = la.id AND lt.status = 'posted' THEN lt.amount ELSE 0 END), 0) as balance
FROM logical_accounts la
LEFT JOIN ledger_transactions lt ON (la.id = lt.debit_account_id OR la.id = lt.credit_account_id)
WHERE la.status = 'active'
GROUP BY la.id, la.account_code, la.account_name, la.account_type;

-- Insert some default accounts for testing
INSERT INTO logical_accounts (account_code, account_name, account_type, currency, created_by) VALUES
    ('1000', 'Cash', 'asset', 'USD', 'system'),
    ('1100', 'Accounts Receivable', 'asset', 'USD', 'system'),
    ('2000', 'Accounts Payable', 'liability', 'USD', 'system'),
    ('3000', 'Equity', 'equity', 'USD', 'system'),
    ('4000', 'Revenue', 'revenue', 'USD', 'system'),
    ('5000', 'Expenses', 'expense', 'USD', 'system')
ON CONFLICT (account_code) DO NOTHING;

-- Grant permissions (adjust as needed for your security model)
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO ledger_api_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ledger_api_user;

COMMENT ON TABLE logical_accounts IS 'Stores account definitions and metadata for the ledger system';
COMMENT ON TABLE ledger_transactions IS 'Stores all financial transactions using double-entry accounting principles';
COMMENT ON TABLE allocation_rules IS 'Stores rules for automated transaction allocation';
COMMENT ON TABLE audit_log IS 'Immutable audit trail of all operations';
COMMENT ON TABLE reconciliation_log IS 'Tracks reconciliation operations and status';
COMMENT ON VIEW account_balances IS 'Provides real-time account balance calculations';
