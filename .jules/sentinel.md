## 2024-03-24 - Excel Formula Injection
**Vulnerability:** Excel Formula Injection (CSV Injection) in `utils/bulk_import.py`.
**Learning:** User inputs (like `=1+1` or `=cmd|...`) that are written back to an Excel file (in this case, an error report) without sanitization can be interpreted as formulas by Excel, potentially leading to command execution or data exfiltration on the administrator's machine. Openpyxl does not automatically sanitize strings starting with `=`.
**Prevention:** Sanitize any string starting with `=`, `+`, `-`, or `@` by prepending a single quote `'` before writing it to an Excel cell.

## 2024-05-22 - Path Traversal in File Uploads
**Vulnerability:** `get_upload_folder` in `services.py` and `views/nhap_lieu.py` constructed file paths using unsanitized user input (`cccd`), allowing potential directory traversal (e.g., `../`) to write files outside the intended directory.
**Learning:** Duplicate logic in Views bypassing centralized checks increases security risk. Even if UI inputs limit length, backend logic must strictly validate all path components.
**Prevention:** Centralize file handling logic in Service layer. Enforce strict allowlist validation (e.g., alphanumeric only) on any user input used to construct file paths.
