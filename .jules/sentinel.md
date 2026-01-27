## 2024-03-24 - Excel Formula Injection
**Vulnerability:** Excel Formula Injection (CSV Injection) in `utils/bulk_import.py`.
**Learning:** User inputs (like `=1+1` or `=cmd|...`) that are written back to an Excel file (in this case, an error report) without sanitization can be interpreted as formulas by Excel, potentially leading to command execution or data exfiltration on the administrator's machine. Openpyxl does not automatically sanitize strings starting with `=`.
**Prevention:** Sanitize any string starting with `=`, `+`, `-`, or `@` by prepending a single quote `'` before writing it to an Excel cell.

## 2024-05-24 - Path Traversal in File Uploads
**Vulnerability:** Path Traversal via unvalidated `cccd` input in `get_upload_folder`.
**Learning:** The application used user-provided identifiers (CCCD) directly in file path construction across multiple views (`nhap_lieu.py`, `ho_so_chi_tiet.py`) and services. This allows malicious actors to read/write files outside the intended directory by supplying inputs like `../`.
**Prevention:** Centralize all file path generation in `services.py` and enforce strict allowlist validation (alphanumeric only) for any user input used in directory names.
