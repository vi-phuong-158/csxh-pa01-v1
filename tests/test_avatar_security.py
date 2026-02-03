import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

from services import save_doi_tuong


class TestAvatarSecurity(unittest.TestCase):
    @patch('services.get_connection')
    @patch('builtins.open')
    @patch('pathlib.Path.mkdir')
    def test_avatar_extension_validation(self, mock_mkdir, mock_open,
                                         mock_get_conn):
        """Test that avatar uploads respect ALLOWED_EXTENSIONS"""

        # Mock DB connection
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        # --- Test case 1: Malicious file extension (.php) ---
        malicious_file = MagicMock()
        malicious_file.name = "exploit.php"
        malicious_file.getbuffer.return_value = b"<?php echo 'hacked'; ?>"

        data_malicious = {
            'cccd': '001099123456',
            'ho_ten': 'Hacker',
            'ngay_sinh': '1990-01-01',
            'gioi_tinh': 'Nam',
            'dia_chi_tinh': 'Phú Thọ',
            'dia_chi_xa': 'Việt Trì',
            'phan_loai_nghe_nghiep': 'Other',
            'chi_tiet_nghe_nghiep': 'None',
            'ghi_chu_chung': 'Test',
            'avatar_file': malicious_file
        }

        save_doi_tuong(data_malicious)

        # Verification: open() should NOT be called for .php file
        self.assertFalse(
            mock_open.called,
            "Should not save files with illegal extensions"
        )

    @patch('services.get_connection')
    @patch('builtins.open')
    @patch('pathlib.Path.mkdir')
    def test_avatar_valid_extension(self, mock_mkdir, mock_open,
                                    mock_get_conn):
        """Test that valid avatar uploads are accepted"""
        # Mock DB connection
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        # --- Test case 2: Valid file extension (.png) ---
        valid_file = MagicMock()
        valid_file.name = "image.png"
        valid_file.getbuffer.return_value = b"fake image data"

        data_valid = {
            'cccd': '001099123456',
            'ho_ten': 'User',
            'ngay_sinh': '1990-01-01',
            'gioi_tinh': 'Nam',
            'dia_chi_tinh': 'Phú Thọ',
            'dia_chi_xa': 'Việt Trì',
            'phan_loai_nghe_nghiep': 'Other',
            'chi_tiet_nghe_nghiep': 'None',
            'ghi_chu_chung': 'Test',
            'avatar_file': valid_file
        }

        save_doi_tuong(data_valid)

        # Verification: open() SHOULD be called for .png file
        self.assertTrue(
            mock_open.called,
            "Should save files with valid extensions"
        )


if __name__ == '__main__':
    unittest.main()
