import os
import unittest

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("DADATA_API_KEY", "test-dadata-api-key")

from handlers import START_TEXT, _build_result_totals, _format_page, _split_for_telegram
from keyboards import CB_PAGE_FOUNDERS, CB_PAGE_SUCCESSOR, CB_PAGE_TAXES


class HandlerSummaryTests(unittest.TestCase):
    def test_start_text_is_short_and_actionable(self):
        self.assertIn("Введите ИНН/ОГРН", START_TEXT)

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


class MaxTariffFieldsTests(unittest.TestCase):
    def setUp(self):
        self.company = {
            "value": "ООО Тест",
            "data": {
                "founders": [{"name": "Иванов И.И.", "share": {"value": "50%"}}],
                "managers": [{"name": "Петров П.П.", "post": "Директор"}],
                "predecessors": [{"name": "ООО Старое", "date": 1609459200000}],
                "successors": [{"name": "ООО Новое", "date": 1640995200000}],
                "tax_system": {"name": "УСН", "code": "6", "date": 1672531200000},
                "branch_count": 3,
            },
        }

    def test_founders_page_shows_expanded_data(self):
        text = _format_page(self.company, CB_PAGE_FOUNDERS)
        self.assertIn("Учредители и руководство", text)
        self.assertIn("Иванов И.И.", text)
        self.assertIn("Петров П.П.", text)
        self.assertIn("ООО Старое", text)
        self.assertIn("ООО Новое", text)

    def test_taxes_page_shows_tax_system(self):
        text = _format_page(self.company, CB_PAGE_TAXES)
        self.assertIn("Налоги и учёт", text)
        self.assertIn("УСН", text)
        self.assertIn("Код системы: 6", text)
        self.assertIn("Количество филиалов: 3", text)

    def test_successor_page_shows_both_directions(self):
        text = _format_page(self.company, CB_PAGE_SUCCESSOR)
        self.assertIn("Правопреемники (1)", text)
        self.assertIn("Правопредшественники (1)", text)


if __name__ == "__main__":
    unittest.main()
