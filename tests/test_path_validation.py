import unittest
from pathlib import Path
import sys
import os

# Add root directory to path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import get_upload_folder, sanitize_filename

class TestSecurity(unittest.TestCase):
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        self.assertEqual(sanitize_filename("test.txt"), "test.txt")
        self.assertEqual(sanitize_filename("../test.txt"), "test.txt")
        # Path().name handles the slash, so test/test.txt becomes test.txt
        self.assertEqual(sanitize_filename("test/test.txt"), "test.txt")

    def test_path_traversal_check(self):
        """Test that get_upload_folder raises ValueError for invalid CCCD"""
        evil_cccd = "../evil_user"

        # Should raise ValueError because it contains non-alphanumeric characters
        with self.assertRaises(ValueError) as cm:
            get_upload_folder(evil_cccd)

        self.assertIn("CCCD không hợp lệ", str(cm.exception))

        # Should also fail for other special chars
        with self.assertRaises(ValueError):
            get_upload_folder("user;rm -rf /")

    def test_valid_cccd(self):
        """Test valid CCCD"""
        valid_cccd = "012345678912"
        folder = get_upload_folder(valid_cccd)
        self.assertTrue(str(folder).endswith(valid_cccd))

if __name__ == '__main__':
    unittest.main()
