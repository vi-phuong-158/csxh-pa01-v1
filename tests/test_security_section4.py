import unittest
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.getcwd())

from views.audit_log import add_audit_log, get_audit_logs, get_action_list
from database import get_connection

class TestSecuritySection4(unittest.TestCase):
    
    def test_config_file_exists(self):
        """Verify .streamlit/config.toml exists"""
        config_path = Path(".streamlit/config.toml")
        self.assertTrue(config_path.exists())
        content = config_path.read_text()
        self.assertIn("enableXsrfProtection = true", content)
        self.assertIn("enableCORS = false", content)

    def test_audit_log_view_action(self):
        """Verify adding 'VIEW' action to audit log"""
        # 1. Verify VIEW is in action list
        actions = get_action_list()
        self.assertIn("VIEW", actions)
        
        # 2. Add a VIEW log
        test_cccd = "TEST_VIEW_CCCD"
        user = "test_audit_user"
        
        success = add_audit_log(
            bang='doi_tuong',
            hanh_dong='VIEW',
            khoa_chinh=test_cccd,
            du_lieu_cu='',
            du_lieu_moi='Test View',
            nguoi_thuc_hien=user
        )
        self.assertTrue(success)
        
        # 3. Verify it exists in DB
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM audit_log WHERE khoa_chinh = ? AND hanh_dong = 'VIEW'", 
            (test_cccd,)
        )
        row = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(row)
        self.assertEqual(row['nguoi_thuc_hien'], user)
        
        # Clean up
        conn = get_connection()
        conn.execute("DELETE FROM audit_log WHERE khoa_chinh = ?", (test_cccd,))
        conn.commit()
        conn.close()

if __name__ == '__main__':
    unittest.main()
