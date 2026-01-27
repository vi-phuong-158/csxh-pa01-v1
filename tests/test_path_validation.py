import unittest
import shutil
from pathlib import Path
import sys
import os

from services import get_upload_folder, sanitize_filename

class TestPathValidation(unittest.TestCase):
    def test_get_upload_folder_traversal(self):
        """Test that get_upload_folder prevents path traversal."""
        # This currently fails (demonstrates vulnerability) or passes if fixed
        # We expect it to RAISE an error or return a safe path if fixed.
        # Current behavior: it probably returns path with ..

        unsafe_cccd = "../evil_directory"

        try:
            folder = get_upload_folder(unsafe_cccd)
            # If we get here without error, check the path
            # We want to ensure it is NOT resolving to outside uploads

            # Resolve to absolute path
            resolved = folder.resolve()
            expected_base = (Path(os.getcwd()) / "uploads").resolve()

            # Check if resolved path is within expected base
            # Note: on some systems .. might be kept if folder doesn't exist,
            # but resolve() usually handles it.

            if not str(resolved).startswith(str(expected_base)):
                self.fail(f"Path traversal detected! Resolved to {resolved}")

        except ValueError as e:
            # If it raises ValueError, that's good (expected behavior)
            pass

    def test_validate_cccd_strict(self):
        """Test strict CCCD validation."""
        # We will implement a validator that only allows alphanumeric
        from services import validate_cccd

        valid_cccd = "123456789012"
        self.assertTrue(validate_cccd(valid_cccd))

        invalid_cccd = "../123"
        self.assertFalse(validate_cccd(invalid_cccd))

        invalid_cccd_2 = "123/456"
        self.assertFalse(validate_cccd(invalid_cccd_2))

if __name__ == '__main__':
    unittest.main()
