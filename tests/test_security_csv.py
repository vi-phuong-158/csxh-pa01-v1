import unittest
import pandas as pd
from utils.security import sanitize_for_excel

class TestSecurityCSV(unittest.TestCase):
    def test_sanitize_normal_string(self):
        self.assertEqual(sanitize_for_excel("Hello World"), "Hello World")
        self.assertEqual(sanitize_for_excel("123456"), "123456")
        self.assertEqual(sanitize_for_excel(""), "")
        self.assertEqual(sanitize_for_excel(None), None)

    def test_sanitize_injection(self):
        self.assertEqual(sanitize_for_excel("=cmd|' /C calc'!A0"), "'=cmd|' /C calc'!A0")
        self.assertEqual(sanitize_for_excel("+1+1"), "'+1+1")
        self.assertEqual(sanitize_for_excel("-1+1"), "'-1+1")
        self.assertEqual(sanitize_for_excel("@SUM(1+1)"), "'@SUM(1+1)")

    def test_pandas_application(self):
        data = {
            'Name': ['Normal', '=Bad'],
            'Value': [123, 456]
        }
        df = pd.DataFrame(data)

        # Apply sanitization
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].apply(sanitize_for_excel)

        self.assertEqual(df.iloc[0]['Name'], "Normal")
        self.assertEqual(df.iloc[1]['Name'], "'=Bad")

if __name__ == '__main__':
    unittest.main()
