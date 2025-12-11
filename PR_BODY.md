# Add Ledger API v1: migrations, FastAPI, allocation engine, tests

## Overview

This PR implements a comprehensive **Ledger API v1** service with double-entry bookkeeping, automated allocation rules, treasury management, and reconciliation services.

## 🎯 Features

### Core Ledger System
- ✅ **Double-entry bookkeeping** with PostgreSQL backend
- ✅ **Five core tables**: logical_accounts, ledger_transactions, allocation_rules, audit_log, reconciliation_log
- ✅ **SQLAlchemy ORM models** with proper relationships and constraints
- ✅ **Alembic migrations** for schema version control

### Allocation Engine
- ✅ **Automated fund distribution** based on configurable percentage rules
- ✅ **Conditional allocations** (e.g., "amount > 1000")
- ✅ **Priority-based rule selection**
- ✅ **Batch transaction tracking** for allocation transparency

### API Endpoints

#### Transactions (`/api/v1/transactions`)
- `POST /` - Create single transaction
- `POST /double-entry` - Create balanced debit/credit pair
- `GET /` - List transactions (filter by account, batch)
- `GET /{transaction_id}` - Get transaction details

#### Treasury (`/api/v1/treasury`)
- `GET /balance` - Get all account balances
- `GET /balance/{account_id}` - Get specific account balance
- `POST /allocate` - Trigger allocation (requires guardian role)
- `GET /report` - Generate comprehensive treasury report

#### Allocation Rules (`/api/v1/allocation-rules`)
- `POST /` - Create allocation rule (requires guardian role)
- `GET /` - List rules (filter by account, active status)
- `GET /{rule_id}` - Get rule details
- `PUT /{rule_id}` - Update rule (requires guardian role)
- `DELETE /{rule_id}` - Soft delete rule (requires guardian role)

### Security & Audit
- ✅ **JWT authentication** with role-based access control
- ✅ **Guardian role** required for sensitive operations
- ✅ **Complete audit trail** for all ledger modifications
- ✅ **Wallet address obfuscation** in logs and documentation (e.g., `jg4c...rgi`)

### Reconciliation
- ✅ **Account reconciliation** service
- ✅ **Discrepancy detection** (duplicates, negative amounts, unbalanced batches)
- ✅ **Reconciliation logging** with detailed results

### Testing & CI/CD
- ✅ **Comprehensive test suite** for allocation service
- ✅ **GitHub Actions workflow** for automated testing
- ✅ **Docker Compose** setup for local development and testing
- ✅ **PostgreSQL integration** in CI pipeline

## 📁 Files Added

### Documentation
- `docs/GUARDIANS.md` - Guardian infrastructure documentation with obfuscated wallet addresses

### Ledger API Core
- `ledger-api/.env.example` - Environment configuration template
- `ledger-api/README.md` - Comprehensive runbook and quickstart guide
- `ledger-api/requirements.txt` - Pinned Python dependencies
- `ledger-api/Dockerfile` - Container build configuration

### Database
- `ledger-api/sql/schema/001_initial_ledger.sql` - Initial schema with all tables, indexes, and triggers
- `ledger-api/alembic.ini` - Alembic configuration
- `ledger-api/alembic/env.py` - Migration environment setup
- `ledger-api/alembic/versions/001_initial_ledger.py` - Initial migration

### Application Code
- `ledger-api/src/config.py` - Settings management
- `ledger-api/src/db/session.py` - Database session handling
- `ledger-api/src/models/models.py` - SQLAlchemy models
- `ledger-api/src/schemas/schemas.py` - Pydantic request/response schemas
- `ledger-api/src/services/allocation.py` - Allocation engine service
- `ledger-api/src/services/reconciliation.py` - Reconciliation service
- `ledger-api/src/deps/auth.py` - JWT authentication dependencies
- `ledger-api/src/hooks/audit.py` - Audit logging hooks
- `ledger-api/src/routes/transactions.py` - Transaction endpoints
- `ledger-api/src/routes/treasury.py` - Treasury endpoints
- `ledger-api/src/routes/allocation_rules.py` - Allocation rules endpoints
- `ledger-api/src/main.py` - FastAPI application entry point

### Testing & CI/CD
- `ledger-api/tests/test_allocation.py` - Allocation service tests
- `.github/workflows/ledger-api-ci.yml` - CI pipeline
- `docker-compose.test.yml` - Docker Compose for testing

## 🔧 Allocation Rules Format

Allocation rules use JSONB format with the following structure:

```json
[
  {
    "destination_account_id": "OPERATIONS",
    "percentage": 50.0,
    "condition": "amount > 1000"
  },
  {
    "destination_account_id": "RESERVE",
    "percentage": 30.0
  },
  {
    "destination_account_id": "DEVELOPMENT",
    "percentage": 20.0
  }
]
```

### Key Features:
- **Percentages must sum to 100%** (validated in Pydantic schema)
- **Conditions are optional** (supports simple comparisons: `amount > X`, `amount < X`)
- **Multiple destinations** supported per rule
- **Priority-based selection** when multiple rules exist

## 🚀 Quick Start

### 1. Set up environment
```bash
cd ledger-api
cp .env.example .env
# Edit .env with your database credentials
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run migrations
```bash
alembic upgrade head
```

### 4. Start the API
```bash
uvicorn src.main:app --reload --port 8001
```

### 5. Access documentation
- API: http://localhost:8001
- Interactive docs: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## 🐳 Docker Compose

Run with Docker:
```bash
docker-compose -f docker-compose.test.yml up ledger-api
```

Run tests:
```bash
docker-compose -f docker-compose.test.yml run ledger-api-test
```

## 🧪 Testing

Run the test suite:
```bash
cd ledger-api
pytest tests/ -v
```

Run allocation tests specifically:
```bash
pytest tests/test_allocation.py -v
```

## 📊 Database Schema

### Tables
1. **logical_accounts** - Chart of accounts (ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE)
2. **ledger_transactions** - All transactions with debit/credit tracking
3. **allocation_rules** - Automated allocation configuration
4. **audit_log** - Complete change history
5. **reconciliation_log** - Reconciliation results and discrepancies

### Default Accounts
- `TREASURY` - Main treasury account (ASSET)
- `OPERATIONS` - Operations fund (EXPENSE)
- `RESERVE` - Reserve fund (ASSET)
- `REVENUE` - Revenue account (REVENUE)

## 🔒 Security

- JWT tokens required for all write operations
- Guardian role required for:
  - Creating/updating/deleting allocation rules
  - Triggering allocations
- Wallet addresses obfuscated in logs (`jg4c...rgi`)
- Complete audit trail for compliance

## 📝 Next Steps

- [ ] Add user authentication/authorization system
- [ ] Implement scheduled reconciliation cron job
- [ ] Add real-time balance calculation views
- [ ] Implement multi-currency support
- [ ] Add transaction reversal functionality
- [ ] Create admin dashboard for rule management

## 🔍 Review Focus Areas

1. **Allocation Logic** - Verify percentage calculations and condition evaluation
2. **Database Schema** - Review indexes and constraints for performance
3. **Authentication** - Validate JWT implementation and role checks
4. **Test Coverage** - Ensure allocation service has comprehensive tests
5. **API Design** - Review endpoint structure and response formats

## 👥 Reviewers

@onenoly1010 @echo-scribe-agent

---

**Status**: 🟡 **DRAFT** - Ready for review, do NOT merge yet
