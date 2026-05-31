# Security Status

**Last Updated:** 2026-05-31
**Repository:** quantum-resonance-clean
**Scope:** frontend dependency audit

## Current Status

The frontend build is verified under Node 22 using `frontend/.nvmrc`.

Completed hardening:

- Pinned frontend runtime to Node 22.
- Removed accidental parent-directory lockfiles that caused Next.js workspace-root warnings.
- Applied safe `npm audit fix` updates.
- Verified production build succeeds with Next.js 16.2.6.
- Reduced local npm audit findings from 6 vulnerabilities, including 3 high, to 4 moderate findings.

## Remaining Findings

`npm audit` still reports 4 moderate findings through this dependency chain:

- `postcss <8.5.10`
- `next`
- `@vercel/analytics`
- `@vercel/speed-insights`

npm suggests `npm audit fix --force`, but that would install `next@9.3.3`, which is a breaking downgrade from the current Next 16 line.

## Policy

Do not run `npm audit fix --force`.

Future remediation should use a controlled upgrade to a patched Next/Vercel dependency chain once available and verified by build tests.

## Verification

Run from `frontend`:

- `nvm use`
- `npm ci`
- `npm run build --if-present`
- `npm audit --audit-level=moderate || true`
