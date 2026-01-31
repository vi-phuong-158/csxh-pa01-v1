## 2026-01-19 - Hardcoded Default Credentials
**Vulnerability:** A hardcoded default password (`admin123`) was present in `auth.py` for the super admin account initialization.
**Learning:** Default credentials are a common vulnerability (CWE-798). While convenient for development, they pose a severe risk if deployed to production without change.
**Prevention:**
1. Use `secrets.token_urlsafe()` to generate random secure passwords during initial setup.
2. Allow overriding via environment variables (`ADMIN_PASSWORD`).
3. Never store default passwords in the source code.

## 2026-01-20 - Unrestricted File Upload & Path Traversal
**Vulnerability:** The `save_doi_tuong` function in `services.py` allowed uploading files with arbitrary extensions (e.g., `.php`) and constructed file paths manually using unvalidated user input (`data['cccd']`), risking path traversal.
**Learning:** Relying on frontend validation (Streamlit's `file_uploader` type check) is insufficient. Backend validation is mandatory. Manual path construction bypasses centralized validation logic.
**Prevention:**
1. Always validate file extensions against an allowlist (`ALLOWED_EXTENSIONS`) on the server side.
2. Use centralized helper functions (like `get_upload_folder`) that enforce validation logic instead of reconstructing paths manually.
