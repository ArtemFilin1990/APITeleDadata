import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("DADATA_API_KEY", "test-dadata-api-key")

import bot


class HealthEndpointsTests(unittest.IsolatedAsyncioTestCase):
    async def test_healthz_returns_ok_with_request_id(self):
        request = SimpleNamespace(headers={"X-Request-Id": "req-123"})
        response = await bot._healthz(request)

        self.assertEqual(response.status, 200)
        self.assertIn(b'"status": "ok"', response.body)
        self.assertIn(b'"request_id": "req-123"', response.body)

    async def test_readyz_returns_503_when_not_ready(self):
        bot.SERVICE_STATUS.ready = False
        bot.SERVICE_STATUS.started_at = None
        request = SimpleNamespace(headers={})

        response = await bot._readyz(request)

        self.assertEqual(response.status, 503)
        self.assertIn(b'"status": "starting"', response.body)


if __name__ == "__main__":
    unittest.main()
