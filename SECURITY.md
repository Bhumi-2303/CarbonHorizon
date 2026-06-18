# Security Policy

## Secret Management Protocol
We take security seriously and have established strict guidelines for managing secrets and credentials within this repository.

### Do NOT Commit Secrets
Under no circumstances should API keys, database URLs, JWT secrets, or any other sensitive credentials be hardcoded in tracked files or committed to version control.

### Using Environment Variables
1. All local development secrets should reside in `.env` files.
2. Ensure that `.env` and `prod_env.yaml` are ignored in `.gitignore`.
3. Use the provided `backend/.env.example` to understand what environment variables are required. 
4. If you add a new environment variable, add it to `.env.example` with a placeholder or fake default value. Never use real values in `.env.example`.

### Production Environments
In production environments (such as Vercel, Heroku, or GitHub Actions), inject secrets using the platform's official secret management functionality (e.g. GitHub Secrets or Vercel Environment Variables).

## Reporting a Vulnerability

If you discover a security vulnerability or a leaked secret, please report it immediately.
DO NOT create a public issue regarding a security vulnerability.
Instead, contact the repository maintainers privately.

If a secret is ever accidentally exposed, it must be rotated immediately in the respective third-party service, and all commits containing the secret must be wiped from history.
