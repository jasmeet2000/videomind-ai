import unittest

from app.core.config import get_settings


class TestCoreConfig(unittest.TestCase):
    def test_get_settings_singleton(self):
        s1 = get_settings()
        s2 = get_settings()
        self.assertIs(s1, s2)
        self.assertEqual(s1.app_name, "VideoMind AI")
        self.assertFalse(s1.debug)


if __name__ == "__main__":
    unittest.main()
