import unittest
import sys
import os

# Add src to Python Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

from infrastructure.updater import GitHubUpdater

class TestGitHubUpdater(unittest.TestCase):
    def setUp(self):
        self.updater = GitHubUpdater()

    def test_version_comparison(self):
        # Format: (remote, local, expected_has_update)
        test_cases = [
            ("1.2.5", "1.2.4", True),
            ("v1.2.5", "1.2.4", True),
            ("1.2.5", "v1.2.4", True),
            ("1.2.5", "1.2.5", False),
            ("1.2.4", "1.2.5", False),
            ("1.3.0", "1.2.9", True),
            ("2.0.0", "1.9.9", True),
            ("1.2.10", "1.2.2", True), # Semver check
            ("1.2.2", "1.2.10", False),
            ("v2.1.0-beta", "v2.0.9", True),
        ]
        for remote, local, expected in test_cases:
            with self.subTest(remote=remote, local=local):
                self.assertEqual(self.updater.compare_version(remote, local), expected)

    def test_invalid_version_fallback(self):
        # Fallback to string comparison or safe failure
        self.assertTrue(self.updater.compare_version("stable", "old"))

if __name__ == "__main__":
    unittest.main()
