import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import save_doi_tuong, ALLOWED_EXTENSIONS

class TestAvatarSecurity(unittest.TestCase):
    def setUp(self):
        # Common data
        self.valid_data = {
            'cccd': '123456789012',
            'ho_ten': 'Test User',
            'ngay_sinh': '1990-01-01',
            'gioi_tinh': 'Nam',
            'dia_chi_tinh': 'Phú Thọ',
            'dia_chi_xa': 'Việt Trì',
            'phan_loai_nghe_nghiep': 'Other',
            'chi_tiet_nghe_nghiep': 'Tester',
            'ghi_chu_chung': '',
        }

    @patch('services.get_connection')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('services.Path')
    def test_upload_malicious_extension_fails(self, mock_path, mock_open, mock_get_conn):
        """
        Test that uploading a file with a disallowed extension (e.g. .php)
        is REJECTED.
        """
        # Mock malicious file
        mock_file = MagicMock()
        mock_file.name = "malicious.php"
        mock_file.getbuffer.return_value = b"<?php echo 'hacked'; ?>"

        data = self.valid_data.copy()
        data['avatar_file'] = mock_file

        # Mock DB connection
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        # Execute
        success, msg = save_doi_tuong(data)

        # Assertion: Should fail
        self.assertFalse(success, "Security check failed: Malicious file was accepted!")
        self.assertIn("Định dạng ảnh không hợp lệ", msg)

        # Verify rollback was called
        mock_conn.rollback.assert_called_once()

        # Verify file was NOT written
        mock_open.assert_not_called()

    @patch('services.get_connection')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('services.Path')
    def test_upload_valid_extension_succeeds(self, mock_path, mock_open, mock_get_conn):
        """
        Test that uploading a file with a valid extension (e.g. .jpg)
        still SUCCEEDS.
        """
        # Mock valid file
        mock_file = MagicMock()
        mock_file.name = "profile.jpg"
        mock_file.getbuffer.return_value = b"image_data"

        data = self.valid_data.copy()
        data['avatar_file'] = mock_file

        # Mock DB connection
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        # Mock filesystem
        mock_path_obj = MagicMock()
        mock_path.return_value = mock_path_obj
        mock_path_obj.parent = mock_path_obj
        mock_path_obj.__truediv__.return_value = mock_path_obj

        # Execute
        success, msg = save_doi_tuong(data)

        # Assertion: Should succeed
        self.assertTrue(success, f"Valid file failed to upload: {msg}")

        # Verify file WAS written
        mock_open.assert_called()

if __name__ == '__main__':
    unittest.main()
