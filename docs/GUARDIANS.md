# Guardians Documentation

> **SECURITY NOTE**: All sensitive wallet addresses and private keys MUST be stored in a secure vault (e.g., Supabase secrets, encrypted key management system). The wallet strings shown below are obfuscated for security. Reference the secure store during deployment.

## Guardian Wallets

The following guardian wallets are configured for this project. Full wallet addresses are stored securely and must never be committed to the repository.

### Primary Guardian
- **Username**: @onenoly1010
- **Wallet Address**: `jg4c...rgi` (obfuscated - retrieve from secure vault)
- **Role**: Primary guardian with full administrative access
- **Permissions**: 
  - Create and modify allocation rules
  - Reconcile treasury accounts
  - Approve critical transactions
  - Access audit logs

### Secondary Guardian
- **Username**: @echo-scribe-agent
- **Wallet Address**: `[REDACTED - store in vault]`
- **Role**: Secondary guardian for review and oversight
- **Permissions**:
  - Review allocation rules
  - View audit logs
  - Reconcile treasury accounts

## Security Best Practices

1. **Never commit secrets**: All private keys and full wallet addresses must be stored in a secure vault
2. **Use environment variables**: Reference secrets via environment variables during deployment
3. **Rotate credentials**: Regularly rotate JWT secrets and API keys
4. **Audit access**: All guardian actions are logged in the audit_log table
5. **Multi-signature**: Consider implementing multi-signature requirements for high-value transactions

## Wallet Integration

Full wallet addresses are required for:
- On-chain transaction verification (TODO: implement Pi Network integration)
- Payment processing
- Balance verification

Retrieve wallet addresses from the secure vault using:
```bash
# Example - replace with actual secure vault commands
vault kv get secret/guardians/primary_wallet
vault kv get secret/guardians/secondary_wallet
```

## On-Chain Verification

Pi Network on-chain verification is currently a TODO and must be integrated separately. All on-chain actions default to testnet until production verification is implemented.

**Testnet Configuration**:
- Network: Pi Testnet
- Explorer: https://testnet.pinet.network
- Verification: Pending implementation

## Access Control

Guardian roles are enforced via JWT tokens with the following claims:
```json
{
  "sub": "guardian_username",
  "roles": ["guardian"],
  "permissions": ["create_allocation_rules", "reconcile_accounts"]
}
```

Sign JWTs using the `GUARDIAN_JWT_SECRET` environment variable (stored securely, not in .env files).
