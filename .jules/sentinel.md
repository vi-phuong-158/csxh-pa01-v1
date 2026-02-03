## 2026-01-19 - Hardcoded Default Credentials
**Vulnerability:** A hardcoded default password (`admin123`) was present in `auth.py` for the super admin account initialization.
**Learning:** Default credentials are a common vulnerability (CWE-798). While convenient for development, they pose a severe risk if deployed to production without change.
**Prevention:**
1. Use `secrets.token_urlsafe()` to generate random secure passwords during initial setup.
2. Allow overriding via environment variables (`ADMIN_PASSWORD`).
3. Never store default passwords in the source code.

## 2026-02-03 - Inconsistent File Extension Validation
**Vulnerability:** Avatar upload in `save_doi_tuong` lacked file extension validation, unlike `save_tai_lieu` which had it. This allowed arbitrary file uploads.
**Learning:** Inconsistent application of security checks across similar features (file uploads) is a common source of vulnerabilities. Developers might secure one entry point but miss another.
**Prevention:**
1. Centralize security logic (e.g., `validate_file_extension`) into reusable utility functions.
2. Apply the same validation logic to all file upload handlers.
