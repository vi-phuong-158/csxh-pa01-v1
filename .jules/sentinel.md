## 2024-03-24 - Excel Formula Injection
**Vulnerability:** Excel Formula Injection (CSV Injection) in `utils/bulk_import.py`.
**Learning:** User inputs (like `=1+1` or `=cmd|...`) that are written back to an Excel file (in this case, an error report) without sanitization can be interpreted as formulas by Excel, potentially leading to command execution or data exfiltration on the administrator's machine. Openpyxl does not automatically sanitize strings starting with `=`.
**Prevention:** Sanitize any string starting with `=`, `+`, `-`, or `@` by prepending a single quote `'` before writing it to an Excel cell.

## 2026-01-22 - Path Traversal via Unvalidated Input
**Vulnerability:** Path Traversal in `services.py` and `views/nhap_lieu.py` where user-provided CCCD (Citizen ID) was used directly in directory paths without sufficient validation.
**Learning:** Even if using `Path` objects, appending user input that contains `..` can lead to traversal if the input is not strictly validated or sanitized. Duplicated logic in views increased the attack surface and made fixes harder to apply globally.
**Prevention:** Strictly validate inputs used in file paths (e.g., allowlist approach, `isdigit()`). Centralize file handling logic in `services.py` and enforce views to import it, preventing vulnerable local reimplementations.
