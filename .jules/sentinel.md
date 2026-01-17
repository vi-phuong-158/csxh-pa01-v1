## 2024-03-24 - Excel Formula Injection
**Vulnerability:** Excel Formula Injection (CSV Injection) in `utils/bulk_import.py`.
**Learning:** User inputs (like `=1+1` or `=cmd|...`) that are written back to an Excel file (in this case, an error report) without sanitization can be interpreted as formulas by Excel, potentially leading to command execution or data exfiltration on the administrator's machine. Openpyxl does not automatically sanitize strings starting with `=`.
**Prevention:** Sanitize any string starting with `=`, `+`, `-`, or `@` by prepending a single quote `'` before writing it to an Excel cell.

## 2026-01-17 - Hardcoded Admin Credentials
**Vulnerability:** Hardcoded default password `admin123` for Super Admin in `auth.py`.
**Learning:** Using hardcoded default credentials (CWE-798) in initialization scripts poses a critical risk if administrators fail to change them immediately. Even if `must_change_password` is enforced, the window of opportunity for an attacker exists.
**Prevention:** Generate secure random passwords using `secrets` module during initialization if no environment variable is provided, and output it securely to the installation logs.
