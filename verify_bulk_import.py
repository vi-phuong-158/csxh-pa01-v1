import sys
import os

sys.path.append(os.getcwd())

print("Checking Bulk Import Refactoring...")

try:
    print("1. Importing utils.bulk_import package...")
    from utils import bulk_import
    print("   [OK] Package imported.")

    print("2. Checking exported members...")
    required = [
        'CSXH_TEMPLATES',
        'TEMPLATE_DEFINITIONS',
        'create_excel_template',
        'validate_excel_data',
        'bulk_import_all',
        'export_error_excel'
    ]
    for item in required:
        if hasattr(bulk_import, item):
            print(f"   [OK] Found {item}")
        else:
            print(f"   [FAIL] Missing {item}")
            sys.exit(1)

    print("3. Checking views.nhap_excel import...")
    from views import nhap_excel
    print("   [OK] views.nhap_excel imported successfully.")

    print("Bulk Import Verification Complete.")

except Exception as e:
    print(f"   [FAIL] Error: {e}")
    sys.exit(1)
