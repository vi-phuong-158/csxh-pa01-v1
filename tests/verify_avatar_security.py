import unittest
from unittest.mock import patch, MagicMock
from services import save_doi_tuong


class TestAvatarSecurity(unittest.TestCase):
    @patch('services.get_connection')
    @patch('builtins.open')
    @patch('services.Path')
    def test_save_doi_tuong_malicious_extension(
            self, mock_path, mock_open, mock_get_conn):
        # Setup mock DB connection
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        # mock_cursor = mock_conn.cursor.return_value # Unused

        # Setup mock file with malicious extension
        mock_file = MagicMock()
        mock_file.name = "exploit.php"
        mock_file.getbuffer.return_value = b"<?php echo 'hacked'; ?>"

        data = {
            'cccd': '123456789012',
            'ho_ten': 'Hacker',
            'ngay_sinh': '2000-01-01',
            'gioi_tinh': 'Nam',
            'dia_chi_tinh': 'Phú Thọ',
            'dia_chi_xa': 'Việt Trì',
            'phan_loai_nghe_nghiep': 'Other',
            'chi_tiet_nghe_nghiep': 'Hacker',
            'ghi_chu_chung': 'Testing exploit',
            'avatar_file': mock_file
        }

        # Mock Path behavior to allow mkdir
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        # We need __file__ to work in services, but since we are mocking Path,
        # Path(__file__).parent / "uploads" ... chain needs to work.
        # This is tricky with chaining.

        # Simpler approach: verify the outcome.

        # Act
        success, msg = save_doi_tuong(data)

        # Assert
        # In vulnerable state: success is True.
        # In fixed state: success should be False.
        self.assertFalse(success, "Should reject malicious file extension")
        self.assertIn("Định dạng ảnh không hỗ trợ", msg)

        # Verify open was NOT called (in fixed state)
        mock_open.assert_not_called()

    @patch('services.get_connection')
    @patch('builtins.open')
    @patch('services.Path')
    def test_save_doi_tuong_valid_extension(
            self, mock_path, mock_open, mock_get_conn):
        # Setup mock DB connection
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        # Setup mock file with VALID extension
        mock_file = MagicMock()
        mock_file.name = "profile.jpg"
        mock_file.getbuffer.return_value = b"image data"

        data = {
            'cccd': '123456789012',
            'ho_ten': 'Good User',
            'ngay_sinh': '2000-01-01',
            'gioi_tinh': 'Nam',
            'dia_chi_tinh': 'Phú Thọ',
            'dia_chi_xa': 'Việt Trì',
            'phan_loai_nghe_nghiep': 'Other',
            'chi_tiet_nghe_nghiep': 'Worker',
            'ghi_chu_chung': 'Valid upload',
            'avatar_file': mock_file
        }

        # Mock Path behavior
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance

        # Act
        success, msg = save_doi_tuong(data)

        # Assert
        self.assertTrue(success, "Should accept valid file extension")
        self.assertEqual(msg, "Lưu thành công!")

        # Verify open WAS called
        mock_open.assert_called()


if __name__ == '__main__':
    unittest.main()
