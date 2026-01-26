from services import get_upload_folder, validate_cccd
import unittest
from pathlib import Path
import shutil
import os
import sys

# Add current directory to path so we can import services
sys.path.append(os.getcwd())


class TestSecurityFix(unittest.TestCase):
    def test_validate_cccd(self):
        # Valid cases
        self.assertTrue(validate_cccd("123456789012"))
        self.assertTrue(validate_cccd("012345678912"))

        # Invalid cases
        self.assertFalse(validate_cccd("123/456"))
        self.assertFalse(validate_cccd("../hacker"))
        self.assertFalse(validate_cccd("..\\hacker"))
        self.assertFalse(validate_cccd(""))
        self.assertFalse(validate_cccd(None))

        # Non-alphanumeric (spaces, dashes) - currently disallowed by isalnum()
        self.assertFalse(validate_cccd("123-456"))
        self.assertFalse(validate_cccd("123 456"))

    def test_get_upload_folder_valid(self):
        cccd = "123456789012"
        folder = get_upload_folder(cccd)
        expected_part = f"uploads/{cccd}"
        self.assertTrue(str(folder).endswith(expected_part))
        self.assertTrue(folder.exists())

        # Cleanup
        if folder.exists():
            shutil.rmtree(folder)

    def test_get_upload_folder_traversal(self):
        # Try traversal
        malicious_cccd = "../hacker_dir"

        # It should raise ValueError because validate_cccd fails
        with self.assertRaises(ValueError) as cm:
            get_upload_folder(malicious_cccd)
        self.assertEqual(str(cm.exception), "Invalid CCCD format")

        # Ensure directory was not created
        hacker_dir = Path(__file__).parent / "hacker_dir"
        self.assertFalse(hacker_dir.exists())


if __name__ == '__main__':
    unittest.main()
