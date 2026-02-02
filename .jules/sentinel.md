## 2026-01-19 - Hardcoded Default Credentials
**Vulnerability:** A hardcoded default password (`admin123`) was present in `auth.py` for the super admin account initialization.
**Learning:** Default credentials are a common vulnerability (CWE-798). While convenient for development, they pose a severe risk if deployed to production without change.
**Prevention:**
1. Use `secrets.token_urlsafe()` to generate random secure passwords during initial setup.
2. Allow overriding via environment variables (`ADMIN_PASSWORD`).
3. Never store default passwords in the source code.

## 2026-01-20 - Unrestricted File Upload in Avatar Creation
**Vulnerability:** The `save_doi_tuong` function allowed uploading avatar files without validating the file extension, potentially allowing malicious files (like .php) to be saved and executed.
**Learning:** Functions that handle file uploads must always validate the file type/extension against a strict allowlist. Reusing validation logic (like `save_tai_lieu` had) is crucial to avoid missing checks in new features.
**Prevention:**
1. Implement strict file extension checks for ALL upload endpoints.
2. Validate extensions BEFORE processing or saving the file.
3. Use a centralized validation function or decorator to ensure consistency across the application.
