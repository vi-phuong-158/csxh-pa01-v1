import unittest
from unittest.mock import patch, MagicMock
import services

class TestAvatarSecurity(unittest.TestCase):

    @patch('services.get_connection')
    @patch('pathlib.Path.mkdir')
    @patch('builtins.open')
    def test_save_malicious_avatar(self, mock_open, mock_mkdir, mock_get_conn):
        # Mock DB connection
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        # Mock file object from Streamlit
        mock_file = MagicMock()
        mock_file.name = "evil.php"
        mock_file.getbuffer.return_value = b"<?php echo 'hacked'; ?>"

        data = {
            'cccd': '123456789012',
            'ho_ten': 'Hacker',
            'ngay_sinh': '1990-01-01',
            'gioi_tinh': 'Nam',
            'dia_chi_tinh': 'Hanoi',
            'dia_chi_xa': 'Ba Dinh',
            'phan_loai_nghe_nghiep': 'IT',
            'chi_tiet_nghe_nghiep': 'Tester',
            'ghi_chu_chung': '',
            'avatar_file': mock_file
        }

        # Attempt to save
        success, message = services.save_doi_tuong(data)

        # Assertions for SECURITY FIX

        # 1. Function should return False (failure)
        self.assertFalse(success, "Should fail when saving malicious file extension")

        # 2. Message should contain validation error
        self.assertIn("Định dạng ảnh không hợp lệ", message)

        # 3. open() should NOT be called (file not written)
        mock_open.assert_not_called()

        # 4. Transaction should be rolled back
        mock_conn.rollback.assert_called_once()

        # 5. Commit should NOT be called (or if called before, rollback overrides it, but here code path prevents commit)
        mock_conn.commit.assert_not_called()

        print("SUCCESS: Malicious file was blocked correctly.")

    @patch('services.get_connection')
    @patch('pathlib.Path.mkdir')
    @patch('builtins.open')
    def test_save_valid_avatar(self, mock_open, mock_mkdir, mock_get_conn):
        # Mock DB connection
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        # Mock file object from Streamlit
        mock_file = MagicMock()
        mock_file.name = "nice_photo.jpg"
        mock_file.getbuffer.return_value = b"image_data"

        data = {
            'cccd': '123456789012',
            'ho_ten': 'Good User',
            'ngay_sinh': '1990-01-01',
            'gioi_tinh': 'Nam',
            'dia_chi_tinh': 'Hanoi',
            'dia_chi_xa': 'Ba Dinh',
            'phan_loai_nghe_nghiep': 'IT',
            'chi_tiet_nghe_nghiep': 'Tester',
            'ghi_chu_chung': '',
            'avatar_file': mock_file
        }

        # Attempt to save
        success, message = services.save_doi_tuong(data)

        # Assertions for VALID case
        self.assertTrue(success)
        mock_open.assert_called_once()
        mock_conn.commit.assert_called_once()
        print("SUCCESS: Valid file was saved correctly.")

if __name__ == '__main__':
    unittest.main()
