import os
import unittest

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("DADATA_API_KEY", "test-dadata-api-key")

from config import validate_telegram_bot_token


class ConfigSecurityTests(unittest.TestCase):
    def test_validate_telegram_bot_token_accepts_test_token(self):
        self.assertTrue(validate_telegram_bot_token("test-token"))

    def test_validate_telegram_bot_token_accepts_realistic_format(self):
        self.assertTrue(validate_telegram_bot_token("123456789:AbCdEfGhIjKlMnOpQrStUvWxYz_123"))

    def test_validate_telegram_bot_token_rejects_invalid_format(self):
        self.assertFalse(validate_telegram_bot_token("invalid-token"))


if __name__ == "__main__":
    unittest.main()
