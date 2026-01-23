import unittest
import shutil
from pathlib import Path
from services import get_upload_folder

class TestPathValidation(unittest.TestCase):
    def test_valid_cccd(self):
        """Test that a valid CCCD returns a correct path."""
        cccd = "012345678901"
        try:
            path = get_upload_folder(cccd)
            self.assertTrue(path.name == cccd)
            self.assertTrue("uploads" in str(path))
            # Clean up
            if path.exists():
                shutil.rmtree(path)
        except ValueError:
            self.fail("Valid CCCD raised ValueError")

    def test_path_traversal(self):
        """Test that path traversal attempts raise ValueError."""
        malicious_inputs = [
            "../etc",
            "../../usr",
            "012/../012",
            "..",
            "/tmp"
        ]
        for cccd in malicious_inputs:
            with self.assertRaises(ValueError, msg=f"Failed to reject: {cccd}"):
                get_upload_folder(cccd)

    def test_special_characters(self):
        """Test that non-alphanumeric characters raise ValueError."""
        invalid_inputs = [
            "123-456",
            "123 456",
            "admin$",
            "user@name"
        ]
        for cccd in invalid_inputs:
            with self.assertRaises(ValueError, msg=f"Failed to reject: {cccd}"):
                get_upload_folder(cccd)

if __name__ == '__main__':
    unittest.main()
