## 2024-03-24 - Excel Formula Injection
**Vulnerability:** Excel Formula Injection (CSV Injection) in `utils/bulk_import.py`.
**Learning:** User inputs (like `=1+1` or `=cmd|...`) that are written back to an Excel file (in this case, an error report) without sanitization can be interpreted as formulas by Excel, potentially leading to command execution or data exfiltration on the administrator's machine. Openpyxl does not automatically sanitize strings starting with `=`.
**Prevention:** Sanitize any string starting with `=`, `+`, `-`, or `@` by prepending a single quote `'` before writing it to an Excel cell.

## 2024-05-22 - Path Traversal in File Handling
**Vulnerability:** Path Traversal in `services.py` (`get_upload_folder`).
**Learning:** Functions that generate file paths based on user input (like `cccd`) must strictly validate that input before using it in `Path` operations. Relying on frontend validation is insufficient. Even `Path(...).parent` constructs can be bypassed if the dynamic part contains `..`.
**Prevention:** Enforce strict allowlist validation (e.g., `isdigit()` and fixed length) on all ID-based path components at the service layer level.
