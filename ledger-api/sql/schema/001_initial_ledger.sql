-- Ledger API Initial Schema
-- Version: 001
-- Description: Initial ledger database schema with double-entry accounting

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create accounts table (Chart of Accounts)
CREATE TABLE IF NOT EXISTS accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_code VARCHAR(50) UNIQUE NOT NULL,
    account_name VARCHAR(255) NOT NULL,
    account_type VARCHAR(50) NOT NULL CHECK (account_type IN ('ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE')),
    parent_account_id UUID REFERENCES accounts(id),
    currency VARCHAR(3) DEFAULT 'USD',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_number VARCHAR(100) UNIQUE NOT NULL,
    transaction_date DATE NOT NULL,
    description TEXT,
    reference_number VARCHAR(100),
    status VARCHAR(50) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'POSTED', 'VOID', 'RECONCILED')),
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    posted_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create transaction_lines table (journal entries)
CREATE TABLE IF NOT EXISTS transaction_lines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_id UUID NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
    account_id UUID NOT NULL REFERENCES accounts(id),
    line_type VARCHAR(10) NOT NULL CHECK (line_type IN ('DEBIT', 'CREDIT')),
    amount DECIMAL(20, 4) NOT NULL CHECK (amount >= 0),
    currency VARCHAR(3) DEFAULT 'USD',
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create allocation_rules table
CREATE TABLE IF NOT EXISTS allocation_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_name VARCHAR(255) NOT NULL,
    source_account_id UUID REFERENCES accounts(id),
    rules JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    metadata JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT valid_allocation_rules CHECK (jsonb_typeof(rules) = 'array')
);

-- Create treasury_accounts table
CREATE TABLE IF NOT EXISTS treasury_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES accounts(id),
    treasury_type VARCHAR(50) NOT NULL CHECK (treasury_type IN ('MAIN', 'RESERVE', 'OPERATIONAL', 'ESCROW')),
    balance DECIMAL(20, 4) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'USD',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create reconciliations table
CREATE TABLE IF NOT EXISTS reconciliations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES accounts(id),
    reconciliation_date DATE NOT NULL,
    statement_balance DECIMAL(20, 4) NOT NULL,
    ledger_balance DECIMAL(20, 4) NOT NULL,
    difference DECIMAL(20, 4) GENERATED ALWAYS AS (statement_balance - ledger_balance) STORED,
    status VARCHAR(50) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED')),
    reconciled_by VARCHAR(255),
    reconciled_at TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create audit_log table
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL CHECK (action IN ('CREATE', 'UPDATE', 'DELETE', 'READ')),
    user_id VARCHAR(255),
    changes JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_accounts_code ON accounts(account_code);
CREATE INDEX idx_accounts_type ON accounts(account_type);
CREATE INDEX idx_accounts_active ON accounts(is_active);

CREATE INDEX idx_transactions_number ON transactions(transaction_number);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_created_at ON transactions(created_at);

CREATE INDEX idx_transaction_lines_txn ON transaction_lines(transaction_id);
CREATE INDEX idx_transaction_lines_account ON transaction_lines(account_id);
CREATE INDEX idx_transaction_lines_type ON transaction_lines(line_type);

CREATE INDEX idx_allocation_rules_source ON allocation_rules(source_account_id);
CREATE INDEX idx_allocation_rules_active ON allocation_rules(is_active);
CREATE INDEX idx_allocation_rules_priority ON allocation_rules(priority);

CREATE INDEX idx_treasury_accounts_account ON treasury_accounts(account_id);
CREATE INDEX idx_treasury_accounts_type ON treasury_accounts(treasury_type);
CREATE INDEX idx_treasury_accounts_active ON treasury_accounts(is_active);

CREATE INDEX idx_reconciliations_account ON reconciliations(account_id);
CREATE INDEX idx_reconciliations_date ON reconciliations(reconciliation_date);
CREATE INDEX idx_reconciliations_status ON reconciliations(status);

CREATE INDEX idx_audit_log_table_record ON audit_log(table_name, record_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_user ON audit_log(user_id);
CREATE INDEX idx_audit_log_created ON audit_log(created_at);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER update_accounts_updated_at BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_transactions_updated_at BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_allocation_rules_updated_at BEFORE UPDATE ON allocation_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_treasury_accounts_updated_at BEFORE UPDATE ON treasury_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reconciliations_updated_at BEFORE UPDATE ON reconciliations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default accounts
INSERT INTO accounts (account_code, account_name, account_type, currency) VALUES
    ('1000', 'Cash', 'ASSET', 'USD'),
    ('1100', 'Accounts Receivable', 'ASSET', 'USD'),
    ('1200', 'Inventory', 'ASSET', 'USD'),
    ('2000', 'Accounts Payable', 'LIABILITY', 'USD'),
    ('2100', 'Accrued Expenses', 'LIABILITY', 'USD'),
    ('3000', 'Equity', 'EQUITY', 'USD'),
    ('4000', 'Revenue', 'REVENUE', 'USD'),
    ('5000', 'Cost of Goods Sold', 'EXPENSE', 'USD'),
    ('5100', 'Operating Expenses', 'EXPENSE', 'USD'),
    ('TRS-001', 'Main Treasury', 'ASSET', 'USD'),
    ('TRS-002', 'Reserve Treasury', 'ASSET', 'USD')
ON CONFLICT (account_code) DO NOTHING;

-- Create view for account balances
CREATE OR REPLACE VIEW account_balances AS
SELECT 
    a.id,
    a.account_code,
    a.account_name,
    a.account_type,
    a.currency,
    COALESCE(SUM(CASE WHEN tl.line_type = 'DEBIT' THEN tl.amount ELSE 0 END), 0) as total_debits,
    COALESCE(SUM(CASE WHEN tl.line_type = 'CREDIT' THEN tl.amount ELSE 0 END), 0) as total_credits,
    COALESCE(
        CASE 
            WHEN a.account_type IN ('ASSET', 'EXPENSE') THEN 
                SUM(CASE WHEN tl.line_type = 'DEBIT' THEN tl.amount ELSE -tl.amount END)
            ELSE 
                SUM(CASE WHEN tl.line_type = 'CREDIT' THEN tl.amount ELSE -tl.amount END)
        END,
        0
    ) as balance
FROM accounts a
LEFT JOIN transaction_lines tl ON a.id = tl.account_id
LEFT JOIN transactions t ON tl.transaction_id = t.id
WHERE t.status = 'POSTED' OR t.status IS NULL
GROUP BY a.id, a.account_code, a.account_name, a.account_type, a.currency;

-- Grant permissions (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO ledger_api_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ledger_api_user;

COMMENT ON TABLE accounts IS 'Chart of accounts for the ledger system';
COMMENT ON TABLE transactions IS 'Transaction headers for all ledger transactions';
COMMENT ON TABLE transaction_lines IS 'Individual debit and credit lines for transactions';
COMMENT ON TABLE allocation_rules IS 'Rules for automatic transaction allocation';
COMMENT ON TABLE treasury_accounts IS 'Treasury account tracking and management';
COMMENT ON TABLE reconciliations IS 'Account reconciliation records';
COMMENT ON TABLE audit_log IS 'Complete audit trail for all ledger operations';
