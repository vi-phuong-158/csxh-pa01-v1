import unittest
from unittest.mock import patch, MagicMock
import services
from services import save_doi_tuong

class TestAvatarVulnerability(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_db.cursor.return_value = self.mock_cursor

    @patch('services.get_connection')
    @patch('services.open')
    @patch('services.Path')
    def test_save_malicious_avatar(self, mock_path, mock_open, mock_get_conn):
        mock_get_conn.return_value = self.mock_db

        # Mock Path structure
        mock_path_obj = MagicMock()
        mock_path.return_value = mock_path_obj
        mock_path_obj.parent = mock_path_obj # Simplified

        # Mock file object with malicious extension
        mock_file = MagicMock()
        mock_file.name = "exploit.php"
        mock_file.getbuffer.return_value = b"<?php system($_GET['cmd']); ?>"

        data = {
            'cccd': '123456789012',
            'ho_ten': 'Hacker',
            'ngay_sinh': '2000-01-01',
            'gioi_tinh': 'Nam',
            'dia_chi_tinh': 'Hanoi',
            'dia_chi_xa': 'Ba Dinh',
            'phan_loai_nghe_nghiep': 'Other',
            'chi_tiet_nghe_nghiep': 'None',
            'ghi_chu_chung': '',
            'avatar_file': mock_file
        }

        # Run function
        save_doi_tuong(data)

        # Check if the UPDATE query was executed for the avatar
        update_calls = [call for call in self.mock_cursor.execute.call_args_list
                        if "UPDATE doi_tuong SET anh_chan_dung" in call[0][0]]

        self.assertEqual(len(update_calls), 0, "Should NOT have updated avatar path for malicious extension")

        # Also ensure open() was NOT called
        mock_open.assert_not_called()

    @patch('services.get_connection')
    @patch('services.open')
    @patch('services.Path')
    def test_save_valid_avatar(self, mock_path, mock_open, mock_get_conn):
        mock_get_conn.return_value = self.mock_db

        # Mock Path structure
        mock_path_obj = MagicMock()
        mock_path.return_value = mock_path_obj
        mock_path_obj.parent = mock_path_obj

        # Mock file object with valid extension
        mock_file = MagicMock()
        mock_file.name = "profile.jpg"
        mock_file.getbuffer.return_value = b"image data"

        data = {
            'cccd': '123456789012',
            'ho_ten': 'User',
            'ngay_sinh': '2000-01-01',
            'gioi_tinh': 'Nam',
            'dia_chi_tinh': 'Hanoi',
            'dia_chi_xa': 'Ba Dinh',
            'phan_loai_nghe_nghiep': 'Other',
            'chi_tiet_nghe_nghiep': 'None',
            'ghi_chu_chung': '',
            'avatar_file': mock_file
        }

        # Run function
        save_doi_tuong(data)

        # Check if the UPDATE query was executed for the avatar
        update_calls = [call for call in self.mock_cursor.execute.call_args_list
                        if "UPDATE doi_tuong SET anh_chan_dung" in call[0][0]]

        self.assertEqual(len(update_calls), 1, "Should have updated avatar path for valid extension")
        mock_open.assert_called()

if __name__ == '__main__':
    unittest.main()
