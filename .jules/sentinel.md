## 2026-01-19 - Hardcoded Default Credentials
**Vulnerability:** A hardcoded default password (`admin123`) was present in `auth.py` for the super admin account initialization.
**Learning:** Default credentials are a common vulnerability (CWE-798). While convenient for development, they pose a severe risk if deployed to production without change.
**Prevention:**
1. Use `secrets.token_urlsafe()` to generate random secure passwords during initial setup.
2. Allow overriding via environment variables (`ADMIN_PASSWORD`).
3. Never store default passwords in the source code.

## 2026-02-04 - Unrestricted File Upload in Avatar Service
**Vulnerability:** `save_doi_tuong` in `services.py` allowed uploading files with arbitrary extensions (e.g., `.php`) as avatars. It accepted the filename extension blindly without validation.
**Learning:** Security checks often exist in main file upload handlers (like `save_tai_lieu`) but are missed in "helper" logic or secondary flows (like avatar updates embedded in profile creation).
**Prevention:**
1. Enforce a strict allowlist (`ALLOWED_EXTENSIONS`) for *all* file upload points.
2. Centralize file validation logic into a helper function (e.g., `validate_upload_file(file)`) and reuse it everywhere.
3. Never trust `file.name` or user-provided extensions without verification.
