import os
import unittest

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("DADATA_API_KEY", "test-dadata-api-key")

from handlers import START_TEXT, _build_result_totals, _split_for_telegram


class HandlerSummaryTests(unittest.TestCase):
    def test_start_text_mentions_fast_and_legal_data(self):
        self.assertIn("Бесплатный быстрый сервис проверки контрагентов", START_TEXT)
        self.assertIn("Только легальные данные", START_TEXT)

    def test_build_result_totals_with_mixed_invalid_values(self):
        text = _build_result_totals(found=1, not_found=0, invalid=["12AB", "123"])
        self.assertIn("Итог: найдено 1, не найдено 0.", text)
        self.assertIn("не только цифры: 12AB", text)
        self.assertIn("неверная длина: 123", text)


class TelegramSplitTests(unittest.TestCase):
    def test_split_for_telegram_respects_limit(self):
        text = ("строка\n" * 30).strip()
        chunks = _split_for_telegram(text, chunk_size=50)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= 50 for chunk in chunks))


if __name__ == "__main__":
    unittest.main()
