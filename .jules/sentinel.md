## 2024-03-24 - Excel Formula Injection
**Vulnerability:** Excel Formula Injection (CSV Injection) in `utils/bulk_import.py`.
**Learning:** User inputs (like `=1+1` or `=cmd|...`) that are written back to an Excel file (in this case, an error report) without sanitization can be interpreted as formulas by Excel, potentially leading to command execution or data exfiltration on the administrator's machine. Openpyxl does not automatically sanitize strings starting with `=`.
**Prevention:** Sanitize any string starting with `=`, `+`, `-`, or `@` by prepending a single quote `'` before writing it to an Excel cell.

## 2024-03-26 - Path Traversal in File Uploads
**Vulnerability:** Path Traversal via `cccd` input field in `views/nhap_lieu.py` and `services.py`. The application constructed file paths using `uploads/{cccd}/{filename}` without strict validation on `cccd`. A malicious user could input `../../path/to/target` as CCCD, leading to arbitrary directory creation and file writing outside the intended `uploads` directory.
**Learning:** Relying on implicit validation or weak checks (like `len(cccd) == 12` which doesn't check for digits) is insufficient. Duplicated logic in View layers (local helper functions) increases the attack surface and makes patching difficult.
**Prevention:**
1. Centralize sensitive logic (file path generation) in a Service layer (`services.py`).
2. Implement strict allowlist validation (e.g., `cccd.isdigit()`) before using input in file paths.
3. Use `Path(filename).name` to sanitize filenames instead of weak `replace` patterns.
