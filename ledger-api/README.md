# Ledger API Service

A production-ready ledger and treasury management API service for the Quantum Resonance Clean project.

## Overview

The Ledger API provides a comprehensive double-entry accounting system with:
- Multi-currency transaction tracking
- Automated allocation rules
- Treasury management
- Reconciliation workflows
- Audit logging
- Role-based access control

## Features

- **Double-Entry Accounting**: Complete ledger with debits and credits
- **Allocation Rules**: Automatic transaction allocation using JSONB rules
- **Treasury Management**: Track treasury accounts and balances
- **Reconciliation**: Built-in reconciliation workflows
- **Audit Trail**: Complete audit logging for compliance
- **PostgreSQL Backend**: Robust database with JSONB support

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+ (with JSONB support)
- pip and virtualenv

### Installation

1. **Navigate to the ledger-api directory**:
   ```bash
   cd ledger-api
   ```

2. **Create and activate virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\Activate.ps1  # Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

   **⚠️ IMPORTANT: Never commit the `.env` file to version control!**

5. **Initialize database**:
   ```bash
   # Run the initial schema
   psql -U your_user -d your_database -f sql/schema/001_initial_ledger.sql
   
   # Run Alembic migrations
   alembic upgrade head
   ```

6. **Start the service**:
   ```bash
   uvicorn src.main:app --reload --port 8001
   ```

### Development Mode

```bash
# Run with auto-reload
uvicorn src.main:app --reload --port 8001

# Run with specific host
uvicorn src.main:app --host 0.0.0.0 --port 8001
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_allocation.py -v
```

## API Endpoints

Once running, access the API documentation at:
- **Interactive Docs**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

### Main Endpoints

- `POST /api/v1/transactions` - Create new transaction
- `GET /api/v1/transactions/{id}` - Get transaction details
- `GET /api/v1/treasury/balance` - Get treasury balance
- `POST /api/v1/allocation-rules` - Create allocation rule
- `GET /api/v1/allocation-rules` - List allocation rules

## Configuration

Edit `.env` file for configuration:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ledger_db

# API Settings
API_SECRET_KEY=your-secret-key-here
API_TITLE=Ledger API
API_VERSION=1.0.0

# Authentication
AUTH_ENABLED=true
JWT_SECRET=your-jwt-secret

# Logging
LOG_LEVEL=INFO
```

## Database Schema

The service uses PostgreSQL with the following main tables:
- `accounts` - Chart of accounts
- `transactions` - Transaction headers
- `transaction_lines` - Transaction line items (debits/credits)
- `allocation_rules` - JSONB-based allocation rules
- `treasury_accounts` - Treasury account tracking
- `reconciliations` - Reconciliation records
- `audit_log` - Complete audit trail

## Allocation Rules Format

Allocation rules use JSONB format:

```json
[
  {
    "destination_account_id": "acc_123",
    "percentage": 50.0,
    "priority": 1
  },
  {
    "destination_account_id": "acc_456",
    "percentage": 50.0,
    "priority": 2
  }
]
```

## Security Notes

### ⚠️ Critical Security Practices

1. **Never commit secrets**: Always use `.env` files and keep them in `.gitignore`
2. **Use strong passwords**: For database and JWT secrets
3. **Enable authentication**: Set `AUTH_ENABLED=true` in production
4. **Use HTTPS**: Always use TLS/SSL in production
5. **Rotate keys regularly**: Change API keys and secrets periodically
6. **Limit database access**: Use least-privilege principle for DB users
7. **Monitor audit logs**: Regularly review audit trail for suspicious activity

### Environment Variables

Keep these files secure and never commit:
- `.env` - Contains secrets
- `*.pem` - SSL certificates
- `*.key` - Private keys

## Project Structure

```
ledger-api/
├── src/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── db/
│   │   └── session.py       # Database session management
│   ├── models/
│   │   └── models.py        # SQLAlchemy models
│   ├── schemas/
│   │   └── schemas.py       # Pydantic schemas
│   ├── services/
│   │   ├── allocation.py    # Allocation service
│   │   └── reconciliation.py # Reconciliation service
│   ├── deps/
│   │   └── auth.py          # Authentication dependencies
│   ├── hooks/
│   │   └── audit.py         # Audit logging hooks
│   └── routes/
│       ├── transactions.py  # Transaction endpoints
│       ├── treasury.py      # Treasury endpoints
│       └── allocation_rules.py # Allocation rules endpoints
├── alembic/                 # Database migrations
├── sql/
│   └── schema/
│       └── 001_initial_ledger.sql # Initial schema
├── tests/
│   └── test_allocation.py  # Tests
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Troubleshooting

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -U your_user -d your_database -c "SELECT version();"

# Check if database exists
psql -U your_user -l | grep ledger
```

### Migration Issues

```bash
# Check migration status
alembic current

# Show migration history
alembic history

# Downgrade one revision
alembic downgrade -1
```

### Common Errors

1. **Import errors**: Ensure virtual environment is activated
2. **Database errors**: Check DATABASE_URL in `.env`
3. **Port conflicts**: Change port in uvicorn command
4. **Permission errors**: Check file permissions and database access

## Contributing

When contributing to this service:
1. Follow existing code structure
2. Add tests for new features
3. Update this README for new functionality
4. Never commit secrets or credentials
5. Use type hints and docstrings

## License

Part of the Quantum Resonance Clean project.

## Support

For issues and questions:
- Check the logs in `logs/` directory
- Review API documentation at `/docs`
- Check database connectivity
- Verify environment variables

---

**Remember: Security is paramount. Never commit credentials, always use environment variables, and follow secure coding practices.**
