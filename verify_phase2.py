import sys
import os

sys.path.append(os.getcwd())

print("Checking Phase 2 Refactoring...")

try:
    print("1. Importing views.profile...")
    from views import profile
    print("   [OK] views.profile imported.")
except Exception as e:
    print(f"   [FAIL] views.profile import error: {e}")

try:
    print("2. Importing components from views.profile...")
    from views.profile import page_profile_view, get_doi_tuong_detail
    print("   [OK] components imported.")
except Exception as e:
    print(f"   [FAIL] component import error: {e}")

try:
    print("3. Checking views.nhap_lieu package...")
    from views import nhap_lieu
    if hasattr(nhap_lieu, 'page_nhap_lieu'):
         print("   [OK] nhap_lieu package imported and exposes 'page_nhap_lieu'.")
    else:
         print("   [FAIL] nhap_lieu missing 'page_nhap_lieu'.")
except Exception as e:
    print(f"   [FAIL] views.nhap_lieu check error: {e}")

print("Phase 2 Verification Complete.")
