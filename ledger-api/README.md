# Ledger API v1

## Overview

The Ledger API provides a single source of truth for ledger transactions, allocation rules, treasury balances, reconciliation, and audit logs for the Quantum Resonance application.

## Features

- **Transaction Management**: Create and track ledger transactions with support for multiple currencies
- **Allocation Engine**: Automatically split transactions based on configurable rules
- **Treasury Management**: Real-time treasury balance tracking and status reporting
- **Reconciliation**: Compare internal balances with external sources and log discrepancies
- **Audit Trail**: Complete audit log of all operations for compliance and debugging
- **Security**: JWT-based authentication with role-based access control

## Security & Secrets Management

⚠️ **IMPORTANT SECURITY NOTES**:

1. **No Secrets in Code**: This repository contains NO private keys, wallet secrets, or sensitive credentials
2. **Wallet Address Redaction**: All wallet addresses in documentation are redacted (e.g., `GDxxx...xxxx`)
3. **Secret Storage**: All sensitive values MUST be stored in:
   - **Supabase Secrets Manager** (recommended for production)
   - **Encrypted Vault** (e.g., HashiCorp Vault, AWS Secrets Manager)
4. **Environment Variables**: Use `.env.example` as a template. Never commit `.env` files with real secrets

### Setting Up Secrets

```bash
# In Supabase dashboard:
# 1. Navigate to Project Settings > Vault
# 2. Add secrets:
#    - guardian_jwt_secret
#    - treasury_wallet_address
#    - database_password

# Reference in application:
# Use environment variable references like:
# GUARDIAN_JWT_SECRET=${SUPABASE_SECRET:guardian_jwt_secret}
```

## Local Development Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- pip or uv

### Installation

1. **Clone and navigate to the ledger-api directory**:
   ```bash
   cd ledger-api
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -e .
   # Or with dev dependencies:
   pip install -e ".[dev]"
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your local configuration
   # NEVER commit real secrets!
   ```

5. **Set up database**:
   ```bash
   # Create database
   createdb ledger_db
   
   # Run migrations
   alembic upgrade head
   ```

### Running Locally

```bash
# Development mode with auto-reload
uvicorn src.main:app --reload --port 8001

# Or using the config from .env
python -m uvicorn src.main:app --reload
```

Access the API:
- **API Docs**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **Health Check**: http://localhost:8001/health

## Database Schema

The ledger uses the following main tables:

- **logical_accounts**: Account definitions with balances
- **ledger_transactions**: All transaction records with metadata
- **allocation_rules**: Rules for automatic transaction splitting
- **audit_log**: Comprehensive audit trail
- **reconciliation_log**: External vs internal balance comparison records

See `sql/schema/001_initial_ledger.sql` for complete schema.

## API Endpoints

### Transactions
- `POST /api/v1/transactions` - Create a new transaction (with automatic allocation)
- `GET /api/v1/transactions` - List and filter transactions

### Treasury
- `GET /api/v1/treasury/status` - Get all account balances
- `POST /api/v1/treasury/reconcile` - Reconcile external balance

### Allocation Rules (Admin)
- `GET /api/v1/allocation-rules` - List allocation rules
- `POST /api/v1/allocation-rules` - Create allocation rule
- `PUT /api/v1/allocation-rules/{id}` - Update allocation rule
- `DELETE /api/v1/allocation-rules/{id}` - Delete allocation rule

## Allocation Engine

The allocation engine automatically splits transactions based on configured rules:

### Rule Format

```json
{
  "name": "Revenue Split",
  "active": true,
  "rules": [
    {
      "destination_account_id": "uuid-1",
      "percentage": 60.0,
      "description": "Operations"
    },
    {
      "destination_account_id": "uuid-2",
      "percentage": 30.0,
      "description": "Development"
    },
    {
      "destination_account_id": "uuid-3",
      "percentage": 10.0,
      "description": "Reserve"
    }
  ]
}
```

### Validation Rules
- Sum of all percentages must equal exactly 100.0
- All destination accounts must exist
- Allocations are created atomically with parent transaction

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_allocation.py -v
```

## Database Migrations

```bash
# Create a new migration
alembic revision -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

## Reconciliation

The reconciliation service compares internal ledger balances with external sources:

1. Fetch external balance (e.g., from blockchain, bank API)
2. Compare with internal ledger balance
3. Log discrepancy in `reconciliation_log`
4. Optionally create correction transaction if approved

```bash
# Example reconciliation API call
curl -X POST http://localhost:8001/api/v1/treasury/reconcile \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "logical_account_id": "uuid",
    "external_balance": "1000.50",
    "currency": "USD"
  }'
```

## Production Deployment

### Environment Variables

Required production environment variables (store in secure vault):
```
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
GUARDIAN_JWT_SECRET=${SUPABASE_SECRET:guardian_jwt_secret}
TREASURY_WALLET_REF=${SUPABASE_SECRET:treasury_wallet_address}
LOG_LEVEL=INFO
```

### Docker

See `docker-compose.test.yml` for containerized setup example.

## Troubleshooting

### Database Connection Issues
- Verify `DATABASE_URL` format
- Ensure PostgreSQL is running
- Check firewall/network settings

### Migration Errors
- Check `alembic.ini` configuration
- Verify database user has CREATE TABLE permissions
- Review migration SQL in `sql/schema/`

### Authentication Errors
- Verify `GUARDIAN_JWT_SECRET` is set correctly
- Check JWT token expiration
- Ensure correct Authorization header format: `Bearer <token>`

## Contributing

1. Create feature branch from `main`
2. Make changes with tests
3. Ensure all tests pass: `pytest`
4. Submit pull request with description

## License

Part of the Quantum Resonance project.
