# Quantum Resonance Guardians

## Overview

This document outlines the guardian nodes and key infrastructure components for the Quantum Resonance Clean project.

## Guardian Wallets

### Primary Guardian
- **Wallet Address**: `jg4c...rgi` <!-- Obfuscated for security -->
- **Role**: Primary ledger guardian and allocation oversight
- **Status**: Active

## Ledger API Infrastructure

The Ledger API service provides:
- Double-entry bookkeeping system
- Automated allocation rules engine
- Treasury management endpoints
- Comprehensive audit logging
- Reconciliation services

### Security Considerations

- All guardian wallet addresses are obfuscated in documentation
- API authentication required for all sensitive endpoints
- Audit logs track all ledger modifications
- Reconciliation logs ensure data integrity

## Access Control

Guardian-level operations require:
1. Valid API authentication token
2. Guardian role assignment
3. Audit log verification

For more information on the Ledger API, see `ledger-api/README.md`.
