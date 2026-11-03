from django.test import TestCase
from http import HTTPStatus

class HealthEndpointTests(TestCase):
    def test_health_returns_ok(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json(), {"status": "ok"})
