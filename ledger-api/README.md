# Ledger API v1 — Quantum Pi Forge

This service provides a ledger for logical accounts, transactions, allocation rules, reconciliation, and audit logging.

Quickstart (local)
1. Create branch: git checkout -b infra/ledger-api-v1
2. Create a Python venv and install dependencies:
   - python -m venv .venv
   - source .venv/bin/activate
   - pip install -r ledger-api/requirements.txt
3. Copy .env.example to .env and fill values (do NOT commit secrets)
4. Run migrations (Alembic):
   - cd ledger-api
   - alembic upgrade head
5. Run app:
   - uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
6. Run tests:
   - pytest -q

Notes
- Do NOT commit secrets. Use a secure store: Supabase secrets or an encrypted vault.
- GUARDIANS.md wallet strings are obfuscated as `jg4c...rgi`. Store the full wallet in a secure vault and reference it during deployment.
- Pi on-chain verification is left as a TODO and must be integrated separately; on-chain actions are testnet-only by default.

API routes (examples)
- POST /api/v1/transactions
- GET /api/v1/transactions
- GET /api/v1/treasury/status
- POST /api/v1/treasury/reconcile
- GET/POST /api/v1/allocation_rules

Environment variables (see .env.example)
- DATABASE_URL
- GUARDIAN_JWT_SECRET
- ENV (development|production)
