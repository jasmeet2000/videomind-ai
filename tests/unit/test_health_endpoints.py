import unittest

from fastapi.testclient import TestClient

from app.main import create_app


class TestHealthEndpoints(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_health(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("version", data)
        self.assertIn("app_name", data)

    def test_readiness(self):
        res = self.client.get("/health/ready")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("dependencies", data)
        self.assertEqual(data["dependencies"]["postgresql"], "not_configured")


if __name__ == '__main__':
    unittest.main()
