## 2024-03-24 - Excel Formula Injection
**Vulnerability:** Excel Formula Injection (CSV Injection) in `utils/bulk_import.py`.
**Learning:** User inputs (like `=1+1` or `=cmd|...`) that are written back to an Excel file (in this case, an error report) without sanitization can be interpreted as formulas by Excel, potentially leading to command execution or data exfiltration on the administrator's machine. Openpyxl does not automatically sanitize strings starting with `=`.
**Prevention:** Sanitize any string starting with `=`, `+`, `-`, or `@` by prepending a single quote `'` before writing it to an Excel cell.

## 2024-05-22 - Path Traversal in File Uploads
**Vulnerability:** Path Traversal in `get_upload_folder`.
**Learning:** Constructing file paths directly from user input (e.g., `Path("uploads") / user_input`) without validation allows attackers to traverse directories (e.g., `../../etc/passwd`). Relying on UI constraints (like `max_chars`) is insufficient security.
**Prevention:** Always validate user input used in file paths against a strict allowlist (e.g., `isalnum()`). Centralize path construction logic in a single service function (like `services.get_upload_folder`) to ensure consistent validation across the application.
