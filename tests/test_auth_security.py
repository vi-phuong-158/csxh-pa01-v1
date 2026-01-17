
import unittest
import os
import sqlite3
import shutil
from unittest.mock import patch
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
import auth

TEST_DB = "test_security_auth.db"

class TestAuthSecurity(unittest.TestCase):
    def setUp(self):
        # Remove test db if exists
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def tearDown(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_init_super_admin_secure(self):
        """Verify that init_super_admin does NOT use default 'admin123' password"""
        # Patch database path to use test db
        with patch('database.get_db_path', return_value=os.path.abspath(TEST_DB)):
            # Initialize DB tables
            database.create_tables()

            # Run init_super_admin
            # We capture stdout to avoid cluttering test output,
            # though capturing it allows us to verify the password is printed.
            from io import StringIO
            import sys
            captured_output = StringIO()
            sys.stdout = captured_output

            try:
                auth.init_super_admin()
            finally:
                sys.stdout = sys.__stdout__

            # Verify admin exists
            conn = sqlite3.connect(TEST_DB)
            cursor = conn.cursor()
            cursor.execute("SELECT username, password_hash FROM users WHERE username='admin'")
            row = cursor.fetchone()
            conn.close()

            self.assertIsNotNone(row)
            username, password_hash = row
            self.assertEqual(username, 'admin')

            # Verify it is NOT the default unsafe password
            is_default = auth.verify_password('admin123', password_hash)
            self.assertFalse(is_default, "Security Risk: Super Admin password is still 'admin123'")

            # Verify it printed the new password
            output = captured_output.getvalue()
            self.assertIn("[SECURITY]", output)
            self.assertIn("Password:", output)

if __name__ == '__main__':
    unittest.main()
