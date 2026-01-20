## 2024-03-24 - Excel Formula Injection
**Vulnerability:** Excel Formula Injection (CSV Injection) in `utils/bulk_import.py`.
**Learning:** User inputs (like `=1+1` or `=cmd|...`) that are written back to an Excel file (in this case, an error report) without sanitization can be interpreted as formulas by Excel, potentially leading to command execution or data exfiltration on the administrator's machine. Openpyxl does not automatically sanitize strings starting with `=`.
**Prevention:** Sanitize any string starting with `=`, `+`, `-`, or `@` by prepending a single quote `'` before writing it to an Excel cell.

## 2024-05-22 - Path Traversal via Code Duplication
**Vulnerability:** Path Traversal in `get_upload_folder` allowed arbitrary directory creation/write.
**Learning:** The vulnerability existed in `services.py` but was also duplicated in `views/nhap_lieu.py` and `views/ho_so_chi_tiet.py` (via manual path construction). Fixing the service layer was insufficient because views were redefining business logic locally, bypassing the centralized service layer. This violates the "Service Layer" pattern and introduces regression risks.
**Prevention:** Strict input validation (CCCD must be 12 digits) in `services.py` and enforcing usage of the centralized `get_upload_folder` in all Views. Avoid local redefinitions of file handling logic.
