# Ledger API v1

## Overview

The Ledger API is a comprehensive double-entry bookkeeping system with automated allocation rules, treasury management, and reconciliation services built on FastAPI and PostgreSQL.

## Features

- **Double-Entry Ledger**: Complete transaction tracking with debits and credits
- **Allocation Engine**: Automated fund distribution based on configurable rules
- **Treasury Management**: Centralized treasury operations and reporting
- **Audit Logging**: Complete audit trail for all ledger operations
- **Reconciliation**: Automated reconciliation with detailed logging
- **FastAPI**: Modern async API with auto-generated documentation

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- pip

### Installation

1. **Navigate to the ledger-api directory**:
   ```bash
   cd ledger-api
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # or
   .venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and configuration
   ```

5. **Initialize database**:
   ```bash
   # Run the schema migration
   psql -U your_user -d ledger_db -f sql/schema/001_initial_ledger.sql
   
   # Or use Alembic for migrations
   alembic upgrade head
   ```

6. **Start the API server**:
   ```bash
   uvicorn src.main:app --reload --port 8001
   ```

7. **Access the API**:
   - API: http://localhost:8001
   - Interactive Docs: http://localhost:8001/docs
   - ReDoc: http://localhost:8001/redoc

## API Endpoints

### Transactions
- `POST /api/v1/transactions` - Create a new ledger transaction
- `GET /api/v1/transactions` - List transactions
- `GET /api/v1/transactions/{id}` - Get transaction details

### Treasury
- `GET /api/v1/treasury/balance` - Get treasury balance
- `POST /api/v1/treasury/allocate` - Trigger allocation
- `GET /api/v1/treasury/report` - Generate treasury report

### Allocation Rules
- `POST /api/v1/allocation-rules` - Create allocation rule
- `GET /api/v1/allocation-rules` - List allocation rules
- `PUT /api/v1/allocation-rules/{id}` - Update allocation rule
- `DELETE /api/v1/allocation-rules/{id}` - Delete allocation rule

## Database Schema

The ledger uses five main tables:

1. **logical_accounts** - Chart of accounts
2. **ledger_transactions** - All ledger entries
3. **allocation_rules** - Automated distribution rules
4. **audit_log** - Complete audit trail
5. **reconciliation_log** - Reconciliation history

## Allocation Rules Format

Allocation rules use JSONB format:

```json
[
  {
    "destination_account_id": "ACC-001",
    "percentage": 50.0,
    "condition": "amount > 1000"
  },
  {
    "destination_account_id": "ACC-002",
    "percentage": 30.0
  },
  {
    "destination_account_id": "ACC-003",
    "percentage": 20.0
  }
]
```

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

Run specific test file:

```bash
pytest tests/test_allocation.py -v
```

## Development

### Running with Docker Compose

```bash
docker-compose -f ../docker-compose.test.yml up ledger-api
```

### Database Migrations

Create a new migration:

```bash
alembic revision -m "description of changes"
```

Apply migrations:

```bash
alembic upgrade head
```

Rollback migration:

```bash
alembic downgrade -1
```

## Security

- All sensitive endpoints require JWT authentication
- Guardian wallet addresses are obfuscated in logs and documentation
- Audit logs track all modifications
- Database credentials should never be committed to version control

## Configuration

Key environment variables (see `.env.example`):

- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET_KEY` - Secret key for JWT tokens
- `GUARDIAN_WALLET_ADDRESS` - Guardian wallet identifier
- `RECONCILIATION_INTERVAL_HOURS` - Reconciliation frequency

## Support

For issues and questions:
- Review the API documentation at `/docs`
- Check the audit logs for transaction history
- See `../docs/GUARDIANS.md` for infrastructure details

## License

Part of the Quantum Resonance Clean project.
