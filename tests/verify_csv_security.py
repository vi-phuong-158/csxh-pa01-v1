import pandas as pd
import sys
import os

# Add repo root to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.utils.security_utils import sanitize_dataframe_for_csv

def test_sanitize_dataframe():
    # Simulate user data with malicious payload
    data = [
        {"name": "Normal User", "note": "Nothing suspicious"},
        {"name": "Hacker", "note": "=1+1"},
        {"name": "Cmd", "note": "=cmd|' /C calc'!A0"},
        {"name": "Plus", "note": "+2+2"},
        {"name": "Minus", "note": "-3-3"},
        {"name": "At", "note": "@SUM(1,1)"}
    ]

    df = pd.DataFrame(data)

    # Apply sanitization
    sanitized_df = sanitize_dataframe_for_csv(df)

    # Generate CSV
    csv_content = sanitized_df.to_csv(index=False)

    print("Sanitized CSV Content:")
    print(csv_content)

    # Assertions
    # Note: Pandas might quote the fields, so we look for the sanitized value inside quotes or not
    # Ideally, we check the dataframe values directly too.

    assert sanitized_df.iloc[1]['note'] == "'=1+1"
    assert sanitized_df.iloc[2]['note'] == "'=cmd|' /C calc'!A0"

    # Check CSV output contains the escaped version
    if "'=1+1" not in csv_content:
         print("[FAIL] '=1+1 not found in CSV")
         sys.exit(1)

    print("\n[PASS] CSV Sanitization verified successfully.")

if __name__ == "__main__":
    test_sanitize_dataframe()
