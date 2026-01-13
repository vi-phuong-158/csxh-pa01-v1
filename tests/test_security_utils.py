import unittest
import pandas as pd
from utils.security import sanitize_for_excel

class TestSecurityUtils(unittest.TestCase):
    def test_sanitize_for_excel(self):
        # Test dangerous characters
        self.assertEqual(sanitize_for_excel("=1+1"), "'=1+1")
        self.assertEqual(sanitize_for_excel("+1+1"), "'+1+1")
        self.assertEqual(sanitize_for_excel("-1+1"), "'-1+1")
        self.assertEqual(sanitize_for_excel("@SUM(1,1)"), "'@SUM(1,1)")

        # Test safe strings
        self.assertEqual(sanitize_for_excel("Safe String"), "Safe String")
        self.assertEqual(sanitize_for_excel("123"), "123")
        self.assertEqual(sanitize_for_excel(""), "")

        # Test non-string inputs
        self.assertEqual(sanitize_for_excel(123), 123)
        self.assertEqual(sanitize_for_excel(None), None)
        self.assertEqual(sanitize_for_excel(1.5), 1.5)

    def test_sanitize_dataframe(self):
        # Create a dataframe with some dangerous inputs
        data = {
            'Name': ['=cmd|', 'John Doe'],
            'Age': [30, 25],
            'Note': ['@link', 'Normal note']
        }
        df = pd.DataFrame(data)

        # Apply sanitization as done in tra_cuu.py
        df_export = df.copy()
        for col in df_export.select_dtypes(include=['object']).columns:
            df_export[col] = df_export[col].apply(sanitize_for_excel)

        # Check results
        self.assertEqual(df_export.iloc[0]['Name'], "'=cmd|")
        self.assertEqual(df_export.iloc[1]['Name'], "John Doe")
        self.assertEqual(df_export.iloc[0]['Note'], "'@link")
        self.assertEqual(df_export.iloc[1]['Note'], "Normal note")
        # Integers should remain integers
        self.assertEqual(df_export.iloc[0]['Age'], 30)

if __name__ == '__main__':
    unittest.main()
