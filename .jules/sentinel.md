## 2026-01-19 - Hardcoded Default Credentials
**Vulnerability:** A hardcoded default password (`admin123`) was present in `auth.py` for the super admin account initialization.
**Learning:** Default credentials are a common vulnerability (CWE-798). While convenient for development, they pose a severe risk if deployed to production without change.
**Prevention:**
1. Use `secrets.token_urlsafe()` to generate random secure passwords during initial setup.
2. Allow overriding via environment variables (`ADMIN_PASSWORD`).
3. Never store default passwords in the source code.
