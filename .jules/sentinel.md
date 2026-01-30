## 2026-01-19 - Hardcoded Default Credentials
**Vulnerability:** A hardcoded default password (`admin123`) was present in `auth.py` for the super admin account initialization.
**Learning:** Default credentials are a common vulnerability (CWE-798). While convenient for development, they pose a severe risk if deployed to production without change.
**Prevention:**
1. Use `secrets.token_urlsafe()` to generate random secure passwords during initial setup.
2. Allow overriding via environment variables (`ADMIN_PASSWORD`).
3. Never store default passwords in the source code.

## 2026-01-30 - Unrestricted File Upload (Avatar)
**Vulnerability:** The `save_doi_tuong` function in `services.py` allowed uploading avatar files with any extension (e.g., `.php`), leading to potential Remote Code Execution (RCE).
**Learning:** Checking file extensions must be applied consistently across ALL upload points. While `save_tai_lieu` was secure, `save_doi_tuong` was missed because it handled uploads differently (inline with data saving).
**Prevention:**
1. Always validate file extensions against an allowlist (`ALLOWED_EXTENSIONS`) before saving.
2. Centralize file saving logic to a single secure function if possible, or ensure all upload paths reuse the same validation logic.
