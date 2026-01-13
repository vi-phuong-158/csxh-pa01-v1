## 2024-03-24 - Excel Formula Injection
**Vulnerability:** Excel Formula Injection (CSV Injection) in `utils/bulk_import.py`.
**Learning:** User inputs (like `=1+1` or `=cmd|...`) that are written back to an Excel file (in this case, an error report) without sanitization can be interpreted as formulas by Excel, potentially leading to command execution or data exfiltration on the administrator's machine. Openpyxl does not automatically sanitize strings starting with `=`.
**Prevention:** Sanitize any string starting with `=`, `+`, `-`, or `@` by prepending a single quote `'` before writing it to an Excel cell.

## 2024-03-24 - Centralized Excel Sanitization
**Vulnerability:** Excel Formula Injection (CSV Injection) in `views/tra_cuu.py`.
**Learning:** CSV exports are also vulnerable to Formula Injection if opened in Excel. This vulnerability can appear in multiple places (Excel export, CSV export).
**Prevention:** Centralized the sanitization logic into `utils/security.py`'s `sanitize_for_excel` function. Applied this function to all string columns before exporting to CSV/Excel.
