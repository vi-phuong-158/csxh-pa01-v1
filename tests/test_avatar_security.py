import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services import save_doi_tuong

class TestAvatarSecurity(unittest.TestCase):
    @patch('services.get_connection')
    @patch('builtins.open')
    @patch('services.Path.mkdir')
    def test_save_doi_tuong_rejects_php(self, mock_mkdir, mock_open, mock_get_conn):
        """Test that save_doi_tuong rejects avatar with .php extension"""

        # Mock DB connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        # Mock avatar file
        avatar_mock = MagicMock()
        avatar_mock.name = "malicious_script.php"
        avatar_mock.getbuffer.return_value = b"<?php echo 'hacked'; ?>"

        data = {
            'cccd': '001099000001',
            'ho_ten': 'Test Security',
            'ngay_sinh': '1990-01-01',
            'gioi_tinh': 'Nam',
            'dia_chi_tinh': 'Phú Thọ',
            'dia_chi_xa': 'Việt Trì',
            'phan_loai_nghe_nghiep': 'Khác',
            'chi_tiet_nghe_nghiep': 'None',
            'ghi_chu_chung': '',
            'avatar_file': avatar_mock
        }

        # Call function
        save_doi_tuong(data)

        # Assertions
        update_calls = [call for call in mock_cursor.execute.call_args_list
                       if "UPDATE doi_tuong SET anh_chan_dung" in call[0][0]]

        self.assertEqual(len(update_calls), 0, "Security vulnerability: Allowed upload of .php file")

    @patch('services.get_connection')
    @patch('builtins.open')
    @patch('services.Path.mkdir')
    def test_save_doi_tuong_accepts_jpg(self, mock_mkdir, mock_open, mock_get_conn):
        """Test that save_doi_tuong accepts avatar with .jpg extension"""

        # Mock DB connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        # Mock avatar file
        avatar_mock = MagicMock()
        avatar_mock.name = "valid_photo.jpg"
        avatar_mock.getbuffer.return_value = b"fake_image_data"

        data = {
            'cccd': '001099000002',
            'ho_ten': 'Test Valid',
            'ngay_sinh': '1990-01-01',
            'gioi_tinh': 'Nữ',
            'dia_chi_tinh': 'Phú Thọ',
            'dia_chi_xa': 'Việt Trì',
            'phan_loai_nghe_nghiep': 'Khác',
            'chi_tiet_nghe_nghiep': 'None',
            'ghi_chu_chung': '',
            'avatar_file': avatar_mock
        }

        # Call function
        success, msg = save_doi_tuong(data)

        # Assertions
        self.assertTrue(success)

        # Check if UPDATE doi_tuong SET anh_chan_dung ... WAS called
        update_calls = [call for call in mock_cursor.execute.call_args_list
                       if "UPDATE doi_tuong SET anh_chan_dung" in call[0][0]]

        self.assertEqual(len(update_calls), 1, "Should accept upload of .jpg file")

        # Verify arguments to update
        args = update_calls[0][0][1] # tuple of args
        relative_path = args[0]
        self.assertIn("uploads/001099000002/", relative_path)
        self.assertTrue(relative_path.endswith(".jpg"))

if __name__ == '__main__':
    unittest.main()
