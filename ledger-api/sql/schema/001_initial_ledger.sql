-- Ledger API v1 - Initial Schema Migration
-- This creates the core tables for double-entry bookkeeping, allocation rules, and audit logging

-- Create logical_accounts table (Chart of Accounts)
CREATE TABLE IF NOT EXISTS logical_accounts (
    id SERIAL PRIMARY KEY,
    account_id VARCHAR(100) UNIQUE NOT NULL,
    account_name VARCHAR(255) NOT NULL,
    account_type VARCHAR(50) NOT NULL CHECK (account_type IN ('ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE')),
    parent_account_id VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_account_id) REFERENCES logical_accounts(account_id) ON DELETE SET NULL
);

-- Create indexes (unique constraint already creates index for account_id)
CREATE INDEX idx_logical_accounts_type ON logical_accounts(account_type);
CREATE INDEX idx_logical_accounts_parent ON logical_accounts(parent_account_id);

-- Create ledger_transactions table (Transaction Log)
CREATE TABLE IF NOT EXISTS ledger_transactions (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(100) UNIQUE NOT NULL,
    account_id VARCHAR(100) NOT NULL,
    transaction_type VARCHAR(10) NOT NULL CHECK (transaction_type IN ('DEBIT', 'CREDIT')),
    amount NUMERIC(20, 8) NOT NULL CHECK (amount >= 0),
    currency VARCHAR(10) DEFAULT 'USD',
    description TEXT,
    reference_id VARCHAR(100),
    batch_id VARCHAR(100),
    source_system VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    FOREIGN KEY (account_id) REFERENCES logical_accounts(account_id) ON DELETE RESTRICT
);

-- Create indexes (unique constraint already creates index for transaction_id)
CREATE INDEX idx_ledger_transactions_account_id ON ledger_transactions(account_id);
CREATE INDEX idx_ledger_transactions_batch_id ON ledger_transactions(batch_id);
CREATE INDEX idx_ledger_transactions_created_at ON ledger_transactions(created_at);
CREATE INDEX idx_ledger_transactions_reference_id ON ledger_transactions(reference_id);

-- Create allocation_rules table (Automated Allocation Configuration)
CREATE TABLE IF NOT EXISTS allocation_rules (
    id SERIAL PRIMARY KEY,
    rule_id VARCHAR(100) UNIQUE NOT NULL,
    rule_name VARCHAR(255) NOT NULL,
    source_account_id VARCHAR(100) NOT NULL,
    allocation_config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,
    effective_from TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    effective_to TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    FOREIGN KEY (source_account_id) REFERENCES logical_accounts(account_id) ON DELETE RESTRICT
);

-- Create indexes (unique constraint already creates index for rule_id)
CREATE INDEX idx_allocation_rules_source_account ON allocation_rules(source_account_id);
CREATE INDEX idx_allocation_rules_active ON allocation_rules(is_active);
CREATE INDEX idx_allocation_rules_priority ON allocation_rules(priority);

-- Create audit_log table (Complete Audit Trail)
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    audit_id VARCHAR(100) UNIQUE NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    old_value JSONB,
    new_value JSONB,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(50),
    user_agent TEXT,
    metadata JSONB DEFAULT '{}'
);

-- Create indexes for audit log queries
CREATE INDEX idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_log_changed_at ON audit_log(changed_at);
CREATE INDEX idx_audit_log_changed_by ON audit_log(changed_by);
CREATE INDEX idx_audit_log_action ON audit_log(action);

-- Create reconciliation_log table (Reconciliation History)
CREATE TABLE IF NOT EXISTS reconciliation_log (
    id SERIAL PRIMARY KEY,
    reconciliation_id VARCHAR(100) UNIQUE NOT NULL,
    reconciliation_type VARCHAR(50) NOT NULL,
    account_id VARCHAR(100),
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('SUCCESS', 'FAILED', 'PARTIAL')),
    total_records INTEGER DEFAULT 0,
    matched_records INTEGER DEFAULT 0,
    unmatched_records INTEGER DEFAULT 0,
    discrepancies JSONB DEFAULT '[]',
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES logical_accounts(account_id) ON DELETE SET NULL
);

-- Create indexes for reconciliation log
CREATE INDEX idx_reconciliation_log_reconciliation_id ON reconciliation_log(reconciliation_id);
CREATE INDEX idx_reconciliation_log_account_id ON reconciliation_log(account_id);
CREATE INDEX idx_reconciliation_log_status ON reconciliation_log(status);
CREATE INDEX idx_reconciliation_log_created_at ON reconciliation_log(created_at);

-- Insert default accounts for testing
INSERT INTO logical_accounts (account_id, account_name, account_type, metadata) VALUES
    ('TREASURY', 'Main Treasury', 'ASSET', '{"description": "Primary treasury account"}'),
    ('OPERATIONS', 'Operations Fund', 'EXPENSE', '{"description": "Operational expenses"}'),
    ('RESERVE', 'Reserve Fund', 'ASSET', '{"description": "Strategic reserve"}'),
    ('REVENUE', 'Revenue Account', 'REVENUE', '{"description": "Primary revenue account"}')
ON CONFLICT (account_id) DO NOTHING;

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER update_logical_accounts_updated_at
    BEFORE UPDATE ON logical_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_allocation_rules_updated_at
    BEFORE UPDATE ON allocation_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE logical_accounts IS 'Chart of accounts for the ledger system';
COMMENT ON TABLE ledger_transactions IS 'All ledger transactions with double-entry bookkeeping';
COMMENT ON TABLE allocation_rules IS 'Automated allocation rules configuration';
COMMENT ON TABLE audit_log IS 'Complete audit trail of all system changes';
COMMENT ON TABLE reconciliation_log IS 'Reconciliation history and results';
