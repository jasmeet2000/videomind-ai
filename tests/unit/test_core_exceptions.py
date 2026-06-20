import unittest

from app.core import exceptions


class TestCoreExceptions(unittest.TestCase):
    def test_video_not_found_error(self):
        e = exceptions.VideoNotFoundError("vid123")
        self.assertEqual(e.status_code, 404)
        self.assertIn("vid123", e.message)

    def test_configuration_error(self):
        e = exceptions.ConfigurationError("DB_URL", "missing")
        self.assertEqual(e.status_code, 500)
        self.assertIn("DB_URL", e.message)


if __name__ == "__main__":
    unittest.main()
