import os
import unittest

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("DADATA_API_KEY", "test-dadata-api-key")

import bot


class BotStartupRetryTests(unittest.TestCase):
    def test_backoff_uses_minimum_attempt(self):
        self.assertGreaterEqual(bot._backoff_delay_seconds(0), 0.1)

    def test_backoff_grows_exponentially_and_respects_cap(self):
        first = bot._backoff_delay_seconds(1)
        second = bot._backoff_delay_seconds(2)
        self.assertGreaterEqual(second, first)
        self.assertLessEqual(second, bot.BOT_STARTUP_RETRY_MAX_DELAY_SECONDS)


if __name__ == "__main__":
    unittest.main()
