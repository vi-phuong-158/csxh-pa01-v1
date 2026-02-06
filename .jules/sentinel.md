## 2026-01-19 - Hardcoded Default Credentials
**Vulnerability:** A hardcoded default password (`admin123`) was present in `auth.py` for the super admin account initialization.
**Learning:** Default credentials are a common vulnerability (CWE-798). While convenient for development, they pose a severe risk if deployed to production without change.
**Prevention:**
1. Use `secrets.token_urlsafe()` to generate random secure passwords during initial setup.
2. Allow overriding via environment variables (`ADMIN_PASSWORD`).
3. Never store default passwords in the source code.

## 2026-02-05 - Arbitrary File Upload via Avatar
**Vulnerability:** The `save_doi_tuong` function allowed uploading avatar files with any extension (e.g., `.php`, `.exe`) because it only renamed the file but preserved the original extension without validation.
**Learning:** Renaming files (e.g., to a timestamp) prevents file overwrite and some traversal attacks but is insufficient if the extension is not validated. Malicious extensions can lead to Remote Code Execution (RCE) if the server executes them.
**Prevention:** Always validate file extensions against a strict allowlist (e.g., `ALLOWED_EXTENSIONS`) before saving.

## 2026-05-21 - Path Traversal in save_doi_tuong
**Vulnerability:** The `save_doi_tuong` function constructed file paths manually using unvalidated `cccd` input (`Path(...) / cccd`), bypassing the existing `validate_cccd` check found in `get_upload_folder`. This allowed creating directories outside the upload root if `cccd` contained traversal characters (`../`).
**Learning:** Reimplementing logic (DRY violation) often leads to security gaps. If a secure helper function (`get_upload_folder`) exists, it must be used everywhere. Manual path construction is prone to errors.
**Prevention:** Always use centralized helper functions for file path generation. Validate all inputs at the entry point of the service function.
