# 🛡️ GUARDIANS: Security and Wallet Management

> **⚠️ SECURITY NOTICE**: Never commit private keys or unencrypted wallet credentials to the repository. Store all sensitive credentials in a secure secrets vault such as Supabase Vault, GitHub Secrets, or `.env.secrets` (gitignored).

## Guardian Roster

| Role | Guardian | Wallet (Obfuscated) | Responsibilities |
|------|----------|---------------------|------------------|
| **Primary Guardian** | @onenoly1010 | `jg4c...rgi` | Main wallet management, payment authorization |
| **Security Guardian** | TBD | N/A | Security audits, vulnerability assessment |
| **Backup Guardian** | TBD | N/A | Backup wallet custody, disaster recovery |

## Wallet Security Protocol

### Storage Requirements
- **Primary Wallet**: Store in Supabase Vault or equivalent encrypted secrets manager
- **Backup Keys**: Offline hardware wallet or encrypted USB storage
- **Environment Variables**: Use `.env.secrets` (add to `.gitignore`)

### Example `.env.secrets` Structure
```bash
# Pi Network Wallet Configuration
PI_WALLET_ADDRESS=jg4c...rgi  # Public address (safe to share)
PI_WALLET_PRIVATE_KEY=<NEVER_COMMIT_THIS>  # Store in vault only
PI_WALLET_PASSPHRASE=<NEVER_COMMIT_THIS>   # Store in vault only

# API Keys
PI_API_KEY=<SECURE_VAULT_ONLY>
HUGGINGFACE_API_TOKEN=<SECURE_VAULT_ONLY>
```

## Guardian Responsibilities

### Primary Guardian
1. **Wallet Management**
   - Monitor wallet balance and transaction history
   - Authorize payment flows and transfers
   - Maintain backup and recovery procedures

2. **Access Control**
   - Manage API key rotation
   - Review and approve new guardian nominations
   - Coordinate multi-signature requirements (if applicable)

3. **Incident Response**
   - Lead security incident investigations
   - Coordinate with community on breach response
   - Execute recovery protocols

### Security Guardian
1. **Regular Audits**
   - Weekly dependency vulnerability scans
   - Monthly code security reviews
   - Quarterly penetration testing

2. **Monitoring**
   - Real-time alert monitoring
   - Suspicious activity detection
   - Access log reviews

3. **Documentation**
   - Maintain security runbooks
   - Update incident response procedures
   - Document security findings

### Backup Guardian
1. **Redundancy**
   - Maintain backup wallet with limited funds
   - Store recovery phrases securely offline
   - Test recovery procedures quarterly

2. **Disaster Recovery**
   - Execute failover procedures if primary guardian unavailable
   - Coordinate with Primary Guardian on recovery
   - Maintain up-to-date backup documentation

## Security Best Practices

### ✅ DO
- Use hardware wallets for large amounts
- Enable 2FA on all accounts
- Rotate API keys quarterly
- Store secrets in encrypted vaults
- Use obfuscated wallet addresses in documentation
- Maintain offline backups
- Review all transactions before signing

### ❌ DON'T
- Commit private keys to version control
- Share wallet passphrases via unsecured channels
- Reuse passwords across services
- Store credentials in plaintext
- Ignore security alerts
- Skip multi-signature verification for large transactions

## Emergency Procedures

### Compromised Credentials
1. Immediately rotate all affected keys
2. Notify all guardians via secure channel
3. Audit recent transactions
4. Update incident log
5. Review and update security procedures

### Lost Access
1. Initiate backup guardian recovery protocol
2. Verify identity through established channels
3. Execute recovery from backup wallet
4. Document incident and lessons learned

### Suspicious Activity
1. Freeze affected accounts/wallets
2. Analyze transaction history
3. Contact Pi Network support if needed
4. Coordinate community communication
5. Implement additional security measures

## Wallet Information

### Primary Pi Wallet
- **Public Address**: `jg4c...rgi` (full address stored in secure vault)
- **Network**: Pi Network Mainnet
- **Purpose**: Primary payment processing, user transactions
- **Backup**: Yes (offline cold storage)

### Recommended Secure Storage Solutions
1. **Supabase Vault**: For API keys and application secrets
2. **GitHub Secrets**: For CI/CD environment variables
3. **`.env.secrets`**: For local development (gitignored)
4. **Hardware Wallet**: For long-term Pi storage
5. **Encrypted Password Manager**: For recovery phrases and backup codes

## Audit Log

All guardian actions should be logged:
- Wallet access and transactions
- API key rotations
- Security incidents
- Access grant/revoke events

---

*"Security through vigilance, trust through transparency, resilience through redundancy."*
