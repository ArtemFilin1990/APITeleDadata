import os
import unittest

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("DADATA_API_KEY", "test-dadata-api-key")

from handlers import _build_result_totals


class HandlerSummaryTests(unittest.TestCase):
    def test_build_result_totals_with_mixed_invalid_values(self):
        text = _build_result_totals(found=1, not_found=0, invalid=["12AB", "123"])
        self.assertIn("Итог: найдено 1, не найдено 0.", text)
        self.assertIn("не только цифры: 12AB", text)
        self.assertIn("неверная длина: 123", text)


if __name__ == "__main__":
    unittest.main()
