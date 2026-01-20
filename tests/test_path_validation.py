import unittest
from services import get_upload_folder
from pathlib import Path
import shutil
import os

class TestPathValidation(unittest.TestCase):
    def test_valid_cccd(self):
        # Should not raise
        cccd = "012345678901"
        path = get_upload_folder(cccd)
        self.assertEqual(path.name, cccd)
        # Clean up created dir
        if path.exists():
            shutil.rmtree(path)

    def test_invalid_cccd_traversal(self):
        with self.assertRaises(ValueError):
            get_upload_folder("../invalid")

    def test_invalid_cccd_length(self):
        with self.assertRaises(ValueError):
            get_upload_folder("123") # Too short

    def test_invalid_cccd_length_long(self):
        with self.assertRaises(ValueError):
            get_upload_folder("0123456789012") # Too long

    def test_invalid_cccd_chars(self):
        with self.assertRaises(ValueError):
            get_upload_folder("01234567890a") # Non-numeric

if __name__ == '__main__':
    unittest.main()
