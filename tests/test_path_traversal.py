
import unittest
from pathlib import Path
import shutil
import os

from services import get_upload_folder, validate_cccd

class TestPathTraversal(unittest.TestCase):
    def test_get_upload_folder_traversal(self):
        # Malicious CCCD
        malicious_cccd = "../../../etc"

        print(f"Testing malicious input: {malicious_cccd}")

        # This should now RAISE ValueError because of validate_cccd
        with self.assertRaises(ValueError) as cm:
            get_upload_folder(malicious_cccd)

        print(f"Caught expected error: {cm.exception}")
        self.assertIn("alphanumeric", str(cm.exception))

    def test_valid_cccd(self):
        valid_cccd = "123456789012"
        path = get_upload_folder(valid_cccd)
        self.assertTrue("123456789012" in str(path))
        print(f"Valid CCCD path: {path}")

if __name__ == '__main__':
    unittest.main()
