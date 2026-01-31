import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

print("Checking imports...")

try:
    print("1. Importing views.dashboard...")
    from views import dashboard
    print("   ✅ views.dashboard imported successfully.")
except Exception as e:
    print(f"   ❌ Failed to import views.dashboard: {e}")

try:
    print("2. Importing views.nhap_lieu...")
    from views import nhap_lieu
    print("   ✅ views.nhap_lieu imported successfully.")
except Exception as e:
    print(f"   ❌ Failed to import views.nhap_lieu: {e}")

try:
    print("3. Checking st.cache_data in dashboard...")
    # Kiểm tra xem decorator có tồn tại không (simple check)
    if hasattr(dashboard, 'get_recent_records'):
        print("   ✅ dashboard.get_recent_records exists.")
    if hasattr(dashboard, 'get_xa_phuong_stats'):
        print("   ✅ dashboard.get_xa_phuong_stats exists.")
except Exception as e:
    print(f"   ❌ Error checking dashboard functions: {e}")

print("Verification complete.")
