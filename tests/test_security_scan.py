import tempfile
import unittest
from pathlib import Path

from scripts.security_scan import scan_paths


class SecurityScanTests(unittest.TestCase):
    def test_token_shaped_credential_is_reported(self):
        """Removing token detection must allow this GitHub-token-shaped secret through."""
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.txt"
            path.write_text("token = " + "ghp_" + "a" * 36)
            issues = scan_paths([path], Path(temporary))
            self.assertTrue(any("credential" in issue for issue in issues), issues)

    def test_private_key_marker_is_reported(self):
        """Removing private-key detection must allow this key marker through."""
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "key.pem"
            path.write_text("-----BEGIN " + "PRIVATE KEY-----")
            issues = scan_paths([path], Path(temporary))
            self.assertTrue(any("private key" in issue for issue in issues), issues)

    def test_email_outside_public_documentation_is_reported(self):
        """Removing private-email detection must allow this source-file address through."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "internal.txt"
            source.write_text("owner" + "@example.com")
            issues = scan_paths([source], root)
            self.assertTrue(any("email-like" in issue for issue in issues), issues)

    def test_email_in_public_documentation_is_allowed(self):
        """Overbroad email detection would incorrectly reject documented public contact."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            readme = root / "README.md"
            readme.write_text("Contact: hello" + "@example.com")
            self.assertEqual([], scan_paths([readme], root))

    def test_non_utf8_file_is_reported_as_unscannable(self):
        """Silently skipping undecodable tracked content would leave a privacy blind spot."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            opaque = root / "opaque.bin"
            opaque.write_bytes(b"\xff\xfe\x00private")
            issues = scan_paths([opaque], root)
            self.assertTrue(any("could not scan as UTF-8 text" in issue for issue in issues), issues)


if __name__ == "__main__":
    unittest.main()
