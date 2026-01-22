import unittest
from pathlib import Path
from services import get_upload_folder, validate_cccd

class TestPathValidation(unittest.TestCase):
    def test_valid_cccd(self):
        """Test that a valid 12-digit CCCD is accepted."""
        cccd = "123456789012"
        try:
            path = get_upload_folder(cccd)
            self.assertIn(cccd, str(path))
            self.assertTrue(str(path).endswith(cccd))
        except ValueError:
            self.fail("Valid CCCD raised ValueError")

    def test_invalid_cccd_length(self):
        """Test that CCCD with incorrect length raises ValueError."""
        invalid_cccds = ["123", "1234567890123", ""]
        for cccd in invalid_cccds:
            with self.assertRaises(ValueError):
                validate_cccd(cccd)
            with self.assertRaises(ValueError):
                get_upload_folder(cccd)

    def test_invalid_cccd_characters(self):
        """Test that CCCD with non-digits raises ValueError."""
        invalid_cccds = ["12345678901a", "abcdefghijkl", "12.34.56.78.", "../........."]
        for cccd in invalid_cccds:
            with self.assertRaises(ValueError):
                validate_cccd(cccd)
            with self.assertRaises(ValueError):
                get_upload_folder(cccd)

    def test_path_traversal_attempt(self):
        """Test that path traversal attempts are blocked."""
        # 12 characters but contains path traversal chars
        # strict digit check should block this anyway
        traversal_payloads = [
            "../etc/passw",
            "..\\..\\win",
            "..../..../.."
        ]
        for payload in traversal_payloads:
            with self.assertRaises(ValueError):
                get_upload_folder(payload)

if __name__ == '__main__':
    unittest.main()
