## 2024-03-24 - Excel Formula Injection
**Vulnerability:** Excel Formula Injection (CSV Injection) in `utils/bulk_import.py`.
**Learning:** User inputs (like `=1+1` or `=cmd|...`) that are written back to an Excel file (in this case, an error report) without sanitization can be interpreted as formulas by Excel, potentially leading to command execution or data exfiltration on the administrator's machine. Openpyxl does not automatically sanitize strings starting with `=`.
**Prevention:** Sanitize any string starting with `=`, `+`, `-`, or `@` by prepending a single quote `'` before writing it to an Excel cell.

## 2024-05-22 - Reusable CSV Injection Prevention
**Vulnerability:** CSV Injection (Excel Formula Injection) in `views/tra_cuu.py` and `views/ra_soat.py`.
**Learning:** Directly exporting DataFrames to CSV using `to_csv` allows malicious input (starting with `=`, `+`, `-`, `@`) to be executed as formulas in Excel.
**Prevention:** Created `utils/security_utils.py` with `sanitize_dataframe_for_csv` to centralize sanitization logic. Always sanitize DataFrames before export.
