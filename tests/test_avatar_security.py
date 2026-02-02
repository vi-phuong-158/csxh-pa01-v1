import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import from root modules
try:
    from services import save_doi_tuong
    from constants import ALLOWED_EXTENSIONS
except ImportError:
    # Fallback if structure is different
    from app.services import save_doi_tuong
    from app.constants import ALLOWED_EXTENSIONS

class TestAvatarSecurity(unittest.TestCase):

    @patch('services.get_connection')
    @patch('builtins.open')
    @patch('services.Path')
    def test_avatar_extension_bypass(self, mock_path, mock_open, mock_get_connection):
        """
        Verify that save_doi_tuong currently accepts any file extension for avatar,
        bypassing ALLOWED_EXTENSIONS.
        """
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock Path to exist
        mock_path_obj = MagicMock()
        mock_path.return_value = mock_path_obj
        mock_path_obj.__truediv__.return_value = mock_path_obj # Handling / operator

        # Helper to simulate file upload object (like streamlit UploadedFile)
        class MockUploadedFile:
            def __init__(self, name, content):
                self.name = name
                self.content = content
            def getbuffer(self):
                return self.content.encode('utf-8')

        # Test case: Malicious PHP file
        malicious_filename = "exploit.php"
        malicious_file = MockUploadedFile(malicious_filename, "<?php system($_GET['cmd']); ?>")

        data = {
            'cccd': '123456789012',
            'ho_ten': 'Test User',
            'ngay_sinh': '1990-01-01',
            'gioi_tinh': 'Nam',
            'dia_chi_tinh': 'Test Province',
            'dia_chi_xa': 'Test Commune',
            'phan_loai_nghe_nghiep': 'Other',
            'chi_tiet_nghe_nghiep': 'Tester',
            'ghi_chu_chung': 'Test',
            'avatar_file': malicious_file
        }

        # Run the function
        success, message = save_doi_tuong(data)

        # Assertions
        # 1. Function should FAIL
        self.assertFalse(success, "Function should fail with malicious extension")

        # 2. Verify error message
        self.assertIn("Định dạng không hỗ trợ", message)

        # 3. Verify that NO file writing was attempted
        mock_open.assert_not_called()

        print("\n[SUCCESS] 'save_doi_tuong' rejected the .php file.")

if __name__ == '__main__':
    unittest.main()
