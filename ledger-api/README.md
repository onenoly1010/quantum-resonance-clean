# Ledger API Service

## Overview

The Ledger API service provides a single source of truth for financial operations in the Quantum Resonance system. It manages:

- **Logical Accounts**: Account management and balance tracking
- **Ledger Transactions**: Double-entry accounting transactions
- **Allocation Rules**: Automated transaction allocation logic
- **Audit Log**: Complete audit trail of all operations
- **Reconciliation Log**: Transaction reconciliation tracking

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- pip (Python package manager)

### Installation

1. **Navigate to the ledger-api directory:**
   ```bash
   cd ledger-api
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # or
   .venv\Scripts\Activate.ps1  # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

   **⚠️ IMPORTANT SECURITY NOTE:**
   - **NEVER commit the `.env` file to version control**
   - Keep database credentials, API keys, and secrets secure
   - Use separate credentials for development, staging, and production
   - Rotate secrets regularly
   - Use environment-specific secret management in production

5. **Initialize the database:**
   ```bash
   # Run the schema creation script
   psql -h localhost -U your_user -d your_database -f sql/schema/001_initial_ledger.sql
   ```

6. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

### Running the Service

**Development mode with auto-reload:**
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8001
```

**Production mode:**
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8001 --workers 4
```

### Access the API

Once running, the service is available at:
- **API Base**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## API Endpoints

### Transactions
- `POST /api/v1/transactions` - Create a new ledger transaction
- `GET /api/v1/transactions` - List transactions
- `GET /api/v1/transactions/{id}` - Get transaction details

### Treasury
- `GET /api/v1/treasury/accounts` - List logical accounts
- `GET /api/v1/treasury/balances` - Get account balances
- `POST /api/v1/treasury/accounts` - Create a new account

### Allocation Rules
- `GET /api/v1/allocation-rules` - List allocation rules
- `POST /api/v1/allocation-rules` - Create allocation rule
- `PUT /api/v1/allocation-rules/{id}` - Update allocation rule
- `DELETE /api/v1/allocation-rules/{id}` - Delete allocation rule

## Database Schema

The service uses PostgreSQL with the following core tables:

- `logical_accounts` - Account definitions and metadata
- `ledger_transactions` - All financial transactions
- `allocation_rules` - Rule definitions for automated allocations
- `audit_log` - Complete audit trail
- `reconciliation_log` - Reconciliation tracking

## Architecture

### Directory Structure

```
ledger-api/
├── README.md                 # This file
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
├── sql/
│   └── schema/
│       └── 001_initial_ledger.sql  # Database schema
├── alembic/                 # Database migrations
│   ├── env.py
│   └── versions/
├── src/
│   ├── main.py              # Application entry point
│   ├── config.py            # Configuration management
│   ├── db/
│   │   └── session.py       # Database session management
│   ├── models/
│   │   └── models.py        # SQLAlchemy models
│   ├── schemas/
│   │   └── schemas.py       # Pydantic schemas
│   ├── services/
│   │   ├── allocation.py    # Allocation logic
│   │   └── reconciliation.py # Reconciliation logic
│   ├── deps/
│   │   └── auth.py          # Authentication dependencies
│   ├── hooks/
│   │   └── audit.py         # Audit logging hooks
│   └── routes/
│       ├── transactions.py  # Transaction endpoints
│       ├── treasury.py      # Treasury endpoints
│       └── allocation_rules.py # Allocation rule endpoints
└── tests/
    └── test_allocation.py   # Allocation service tests
```

## Security Best Practices

1. **Environment Variables**
   - Never commit `.env` files
   - Use strong, unique passwords for database
   - Rotate credentials regularly

2. **API Security**
   - Use API key authentication (configured in `deps/auth.py`)
   - Enable HTTPS in production
   - Implement rate limiting
   - Validate all inputs

3. **Database Security**
   - Use connection pooling
   - Implement row-level security where appropriate
   - Regular backups
   - Encrypt sensitive data at rest

4. **Audit Trail**
   - All operations are logged
   - Audit logs are immutable
   - Include user context in all operations

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

Run specific tests:
```bash
pytest tests/test_allocation.py -v
```

## Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running
- Check credentials in `.env`
- Ensure database exists and schema is applied
- Check firewall/network settings

### Port Already in Use
```bash
# Use a different port
uvicorn src.main:app --port 8002
```

### Migration Issues
```bash
# Reset migrations (development only!)
alembic downgrade base
alembic upgrade head
```

## Contributing

When contributing to the Ledger API:

1. Follow PEP 8 style guidelines
2. Add tests for new features
3. Update documentation
4. Ensure all tests pass
5. Never commit secrets or credentials

## Support

For issues and questions:
- Create an issue in the repository
- Check existing documentation
- Review API documentation at `/docs`

## License

This service is part of the Quantum Resonance Clean project.
