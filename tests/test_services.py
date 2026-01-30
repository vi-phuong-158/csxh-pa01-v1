import unittest
import sqlite3
import json
from unittest.mock import patch, MagicMock
from services import (
    validate_cccd,
    sanitize_filename,
    save_doi_tuong,
    check_cccd_exists,
    save_lien_he,
    save_tai_chinh
)


class TestServicesValidation(unittest.TestCase):
    def test_validate_cccd(self):
        """Test validate_cccd function"""
        self.assertTrue(validate_cccd("012345678901"))
        self.assertTrue(validate_cccd("AbCd123"))
        self.assertFalse(validate_cccd("123-456"))  # Hyphen not allowed
        self.assertFalse(validate_cccd("../etc/passwd"))  # Path traversal
        self.assertFalse(validate_cccd(""))
        self.assertFalse(validate_cccd(None))

    def test_sanitize_filename(self):
        """Test sanitize_filename function"""
        self.assertEqual(sanitize_filename("test.jpg"), "test.jpg")
        self.assertEqual(sanitize_filename("../test.jpg"), "test.jpg")
        self.assertEqual(sanitize_filename("test/file.jpg"), "file.jpg")
        # Special chars should be removed
        self.assertEqual(sanitize_filename("test@#$.jpg"), "test.jpg")
        # Unicode should be kept
        self.assertEqual(sanitize_filename("tài liệu.pdf"), "tài liệu.pdf")


class TestServicesDatabase(unittest.TestCase):
    def setUp(self):
        # Create an in-memory database for testing
        self.real_conn = sqlite3.connect(':memory:')
        self.real_conn.row_factory = sqlite3.Row
        cursor = self.real_conn.cursor()

        # Create minimal tables for testing
        cursor.execute("""
            CREATE TABLE doi_tuong (
                cccd TEXT PRIMARY KEY,
                ho_ten TEXT,
                ngay_sinh DATE,
                gioi_tinh TEXT,
                dia_chi_tinh TEXT,
                dia_chi_xa TEXT,
                anh_chan_dung TEXT,
                phan_loai_nghe_nghiep TEXT,
                chi_tiet_nghe_nghiep TEXT,
                ghi_chu_chung TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE lien_he (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cccd TEXT NOT NULL,
                loai_lien_he TEXT,
                gia_tri TEXT,
                ghi_chu TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE tai_chinh (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cccd TEXT NOT NULL,
                ngan_hang TEXT,
                so_tai_khoan TEXT,
                chu_tai_khoan TEXT,
                ghi_chu TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.real_conn.commit()

    def tearDown(self):
        self.real_conn.close()

    def _get_mock_conn(self):
        # Create a mock that wraps the real connection
        # We need to manually side_effect methods that need to return other mocks or behave specifically

        # However, simple MagicMock(wraps=real_conn) might fail for C-extensions like sqlite3 if not careful
        # Let's try to just mock the methods we need: cursor, commit, close

        mock_conn = MagicMock()
        mock_conn.cursor.side_effect = self.real_conn.cursor
        mock_conn.commit.side_effect = self.real_conn.commit
        # close does nothing
        mock_conn.close.return_value = None
        return mock_conn

    @patch('services.get_connection')
    def test_save_doi_tuong(self, mock_get_conn):
        """Test saving a new profile"""
        mock_conn = self._get_mock_conn()
        mock_get_conn.return_value = mock_conn

        data = {
            'cccd': '001099123456',
            'ho_ten': 'Nguyen Van Test',
            'ngay_sinh': '1990-01-01',
            'gioi_tinh': 'Nam',
            'dia_chi_tinh': 'Phú Thọ',
            'dia_chi_xa': 'Việt Trì',
            'phan_loai_nghe_nghiep': 'Kinh doanh',
            'chi_tiet_nghe_nghiep': 'Giám đốc',
            'ghi_chu_chung': 'Test record'
        }

        success, msg = save_doi_tuong(data)
        self.assertTrue(success)
        self.assertEqual(msg, "Lưu thành công!")

        # Verify DB using real connection
        cursor = self.real_conn.cursor()
        cursor.execute("SELECT * FROM doi_tuong WHERE cccd = ?",
                       ('001099123456',))
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row['ho_ten'], 'Nguyen Van Test')

    @patch('services.get_connection')
    def test_check_cccd_exists(self, mock_get_conn):
        """Test checking if CCCD exists"""
        mock_conn = self._get_mock_conn()
        mock_get_conn.return_value = mock_conn

        # Insert a dummy record directly
        cursor = self.real_conn.cursor()
        cursor.execute(
            "INSERT INTO doi_tuong (cccd) VALUES (?)", ('123456789',))
        self.real_conn.commit()

        self.assertTrue(check_cccd_exists('123456789'))
        self.assertFalse(check_cccd_exists('999999999'))

    @patch('services.get_connection')
    def test_save_lien_he(self, mock_get_conn):
        mock_conn = self._get_mock_conn()
        mock_get_conn.return_value = mock_conn

        # First create parent record
        cursor = self.real_conn.cursor()
        cursor.execute(
            "INSERT INTO doi_tuong (cccd) VALUES (?)", ('111222333',))
        self.real_conn.commit()

        result = save_lien_he('111222333', 'Mobile',
                              '0987654321', 'Main phone')
        self.assertTrue(result)

        cursor = self.real_conn.cursor()
        cursor.execute("SELECT * FROM lien_he WHERE cccd = ?", ('111222333',))
        row = cursor.fetchone()
        self.assertEqual(row['gia_tri'], '0987654321')


if __name__ == '__main__':
    unittest.main()
