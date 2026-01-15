## 2024-03-24 - Excel Formula Injection
**Vulnerability:** Excel Formula Injection (CSV Injection) in `utils/bulk_import.py`.
**Learning:** User inputs (like `=1+1` or `=cmd|...`) that are written back to an Excel file (in this case, an error report) without sanitization can be interpreted as formulas by Excel, potentially leading to command execution or data exfiltration on the administrator's machine. Openpyxl does not automatically sanitize strings starting with `=`.
**Prevention:** Sanitize any string starting with `=`, `+`, `-`, or `@` by prepending a single quote `'` before writing it to an Excel cell.
## 2024-05-23 - CSV Injection in Excel Exports
**Vulnerability:** User input starting with =, +, -, or @ can be executed as formulas when exported to CSV/Excel.
**Learning:** Even internal tools need output sanitization for exports, as admin machines are high-value targets.
**Prevention:** Use `utils.security.sanitize_for_excel` on all string columns before `to_csv`.
