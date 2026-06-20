import unittest

from app.core.logging import configure_logging, get_logger


class TestCoreLogging(unittest.TestCase):
    def test_configure_and_get_logger(self):
        # Should not raise
        configure_logging()
        logger = get_logger("tests")
        self.assertIsNotNone(logger)
        self.assertTrue(hasattr(logger, "info"))
        # Logging a message should not raise
        logger.info("unit test log", test_key="value")


if __name__ == "__main__":
    unittest.main()
