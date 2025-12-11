# Ledger API Service

## Overview

The Ledger API Service provides a single source of truth for financial ledger operations including:
- Logical account management
- Ledger transaction tracking
- Allocation rule configuration
- Audit logging
- Reconciliation tracking

## ⚠️ Security Notes

**IMPORTANT: Never commit secrets or sensitive credentials to the repository!**

- All sensitive configuration must be stored in `.env` files (excluded via `.gitignore`)
- Wallet addresses and private keys should be obfuscated in documentation
- Use environment variables for all database credentials, API keys, and secrets
- JWT secrets must be strong and unique per environment
- Admin endpoints require JWT authentication

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- pip and virtualenv

### Installation

1. **Clone the repository and navigate to ledger-api directory**:
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
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your actual configuration
   nano .env
   ```

5. **Initialize the database**:
   ```bash
   # Run the schema creation script
   psql -U your_db_user -d your_db_name -f sql/schema/001_initial_ledger.sql
   
   # Or use Alembic migrations
   alembic upgrade head
   ```

6. **Run the API server**:
   ```bash
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8001
   ```

7. **Access the API documentation**:
   - Swagger UI: http://localhost:8001/docs
   - ReDoc: http://localhost:8001/redoc

## Configuration

The Ledger API uses environment variables for configuration. Copy `.env.example` to `.env` and update with your values:

```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/ledger_db

# JWT Authentication
JWT_SECRET_KEY=your-super-secret-jwt-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# API Configuration
API_V1_PREFIX=/api/v1
ALLOW_ORIGINS=http://localhost:3000,http://localhost:8000

# Server Configuration
HOST=0.0.0.0
PORT=8001
```

## API Endpoints

### Transactions

- `POST /api/v1/transactions` - Create a new transaction
- `GET /api/v1/transactions` - List transactions (with filtering)
- `GET /api/v1/transactions/{id}` - Get transaction details
- `GET /api/v1/transactions/account/{account_id}` - Get account transactions

### Treasury

- `GET /api/v1/treasury/accounts` - List all logical accounts
- `POST /api/v1/treasury/accounts` - Create a logical account (admin)
- `GET /api/v1/treasury/accounts/{id}` - Get account details
- `GET /api/v1/treasury/balance/{account_id}` - Get account balance

### Allocation Rules

- `GET /api/v1/allocation-rules` - List allocation rules
- `POST /api/v1/allocation-rules` - Create allocation rule (admin)
- `GET /api/v1/allocation-rules/{id}` - Get rule details
- `PUT /api/v1/allocation-rules/{id}` - Update rule (admin)
- `POST /api/v1/allocation-rules/{id}/execute` - Execute allocation

## Allocation Rules Format

Allocation rules use JSONB format to define how funds are distributed:

```json
[
  {
    "destination_account_id": "uuid-of-destination-account",
    "percentage": 25.5,
    "priority": 1
  },
  {
    "destination_account_id": "uuid-of-another-account",
    "percentage": 74.5,
    "priority": 2
  }
]
```

- `destination_account_id`: UUID of the target account
- `percentage`: Percentage of funds to allocate (must sum to 100)
- `priority`: Order of allocation (lower numbers first)

## Database Schema

The ledger uses PostgreSQL with the following core tables:

- **logical_accounts**: Account definitions (asset, liability, equity, revenue, expense)
- **ledger_transactions**: All financial transactions
- **allocation_rules**: Automated allocation configurations
- **audit_log**: Complete audit trail of all changes
- **reconciliation_log**: Account reconciliation tracking

See `sql/schema/001_initial_ledger.sql` for the complete schema definition.

## Authentication

Admin endpoints require JWT authentication. Include the token in the Authorization header:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8001/api/v1/treasury/accounts
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_allocation.py
```

## Migrations

The project uses Alembic for database migrations:

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

## Development

### Project Structure

```
ledger-api/
├── sql/
│   └── schema/
│       └── 001_initial_ledger.sql
├── alembic/
│   ├── env.py
│   └── versions/
├── src/
│   ├── config.py
│   ├── main.py
│   ├── db/
│   │   └── session.py
│   ├── models/
│   │   └── models.py
│   ├── schemas/
│   │   └── schemas.py
│   ├── services/
│   │   ├── allocation.py
│   │   └── reconciliation.py
│   ├── deps/
│   │   └── auth.py
│   ├── hooks/
│   │   └── audit.py
│   └── routes/
│       ├── transactions.py
│       ├── treasury.py
│       └── allocation_rules.py
└── tests/
    └── test_allocation.py
```

### Code Style

- Follow PEP 8 guidelines
- Use type hints
- Document functions and classes with docstrings
- Run linters before committing: `black`, `isort`, `flake8`

## Troubleshooting

### Database Connection Issues

1. Verify PostgreSQL is running:
   ```bash
   sudo systemctl status postgresql
   ```

2. Check DATABASE_URL in `.env` is correct

3. Ensure database exists:
   ```bash
   createdb ledger_db
   ```

### Migration Issues

If migrations fail:
```bash
# Reset migrations (WARNING: data loss)
alembic downgrade base
alembic upgrade head
```

### Port Already in Use

Change the port in `.env` or when starting:
```bash
uvicorn src.main:app --port 8002
```

## Production Deployment

### Using Docker

```bash
# Build image
docker build -t ledger-api:latest .

# Run container
docker run -d \
  --env-file .env \
  -p 8001:8001 \
  ledger-api:latest
```

### Environment Considerations

- Use strong, unique JWT secrets
- Enable HTTPS/TLS in production
- Set appropriate CORS origins
- Configure rate limiting
- Enable request logging
- Set up monitoring and alerting
- Regular database backups
- Use connection pooling for database

## Support

For issues or questions:
- Create an issue on GitHub
- Review existing documentation
- Check the API docs at `/docs`

## License

Part of the Quantum Resonance Clean project.
