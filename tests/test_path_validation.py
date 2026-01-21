import unittest
import shutil
from pathlib import Path
from services import get_upload_folder

class TestPathValidation(unittest.TestCase):
    def test_get_upload_folder_valid(self):
        """Test valid CCCD returns correct path"""
        cccd = "123456789012"

        path = get_upload_folder(cccd)
        self.assertTrue(str(path).endswith(f"uploads/{cccd}"))
        self.assertTrue(path.exists())
        # Cleanup
        if path.exists():
            shutil.rmtree(path)

    def test_get_upload_folder_invalid_length(self):
        """Test CCCD with invalid length raises ValueError"""
        with self.assertRaises(ValueError):
            get_upload_folder("123")
        with self.assertRaises(ValueError):
            get_upload_folder("1234567890123")

    def test_get_upload_folder_non_numeric(self):
        """Test non-numeric CCCD raises ValueError"""
        with self.assertRaises(ValueError):
            get_upload_folder("12345678901a")

    def test_get_upload_folder_path_traversal(self):
        """Test path traversal attempt raises ValueError"""
        with self.assertRaises(ValueError):
            get_upload_folder("../123456789012")
        with self.assertRaises(ValueError):
            get_upload_folder("..")
        with self.assertRaises(ValueError):
            get_upload_folder("/etc/passwd")

if __name__ == '__main__':
    unittest.main()
