import os
import unittest

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("DADATA_API_KEY", "test-dadata-api-key")


from keyboards import CB_PAGE_DOCUMENTS, CB_PAGE_FOUNDERS, CB_PAGE_MANAGEMENT, CB_PAGE_TAXES
from handlers import (
    HELP_TEXT,
    START_TEXT,
    _build_all_fields_block,
    _build_details_card,
    _build_result_totals,
    _format_page,
    _money,
    _split_for_telegram,
)


class HandlerSummaryTests(unittest.TestCase):
    def test_start_text_mentions_spy_greeting_and_whisper(self):
        self.assertIn("Агент на связи", START_TEXT)
        self.assertIn("Шёпотом: введи ИНН/ОГРН", START_TEXT)

    def test_build_result_totals_with_mixed_invalid_values(self):
        text = _build_result_totals(found=1, not_found=0, invalid=["12AB", "123"])
        self.assertIn("Итог: найдено 1, не найдено 0.", text)
        self.assertIn("не только цифры: 12AB", text)
        self.assertIn("неверная длина: 123", text)

    def test_help_text_mentions_supported_commands(self):
        self.assertIn("/start", HELP_TEXT)
        self.assertIn("/help", HELP_TEXT)
        self.assertIn("/find", HELP_TEXT)


class TelegramSplitTests(unittest.TestCase):
    def test_split_for_telegram_respects_limit(self):
        text = ("строка\n" * 30).strip()
        chunks = _split_for_telegram(text, chunk_size=50)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= 50 for chunk in chunks))


class PremiumPagesTests(unittest.TestCase):
    def setUp(self):
        self.company = {
            "data": {
                "founders": [
                    {"name": "Иванов И.И.", "share": {"value": 5000}},
                ],
                "management": {"name": "Петров П.П.", "post": "Генеральный директор", "start_date": 1672531200000},
                "managers": [{"name": "Сидоров С.С.", "post": "Директор"}],
                "authorities": {"fts_registration": {"name": "ИФНС №1", "date": 1672531200000}},
                "tax_system": {"name": "УСН"},
                "fns_debt": {"debt": 1200},
                "licenses": [{"series": "77", "number": "123456", "issue_date": 1672531200000}],
                "documents": [{"type": "Устав", "number": "1", "issue_date": 1672531200000}],
            }
        }

    def test_founders_page_renders_data(self):
        text = _format_page(self.company, CB_PAGE_FOUNDERS)
        self.assertIn("Учредители", text)
        self.assertIn("Иванов И.И.", text)

    def test_management_page_renders_current_and_history(self):
        text = _format_page(self.company, CB_PAGE_MANAGEMENT)
        self.assertIn("Текущий руководитель", text)
        self.assertIn("История руководителей", text)

    def test_taxes_page_renders_tax_fields(self):
        text = _format_page(self.company, CB_PAGE_TAXES)
        self.assertIn("Налоговый орган", text)
        self.assertIn("УСН", text)

    def test_documents_page_renders_licenses_and_documents(self):
        text = _format_page(self.company, CB_PAGE_DOCUMENTS)
        self.assertIn("Лицензии", text)
        self.assertIn("Документы", text)

    def test_money_handles_numeric_string(self):
        self.assertEqual(_money("1200"), "1 200 ₽")

    def test_details_card_handles_non_list_premium_fields(self):
        company = {
            "value": 'ООО "Тест"',
            "data": {
                "name": {"short_with_opf": 'ООО "Тест"', "full_with_opf": 'Общество с ограниченной ответственностью "Тест"'},
                "inn": "7707083893",
                "kpp": "770701001",
                "ogrn": "1027700132195",
                "state": {"status": "ACTIVE"},
                "founders": {"unexpected": "dict"},
                "managers": {"unexpected": "dict"},
                "licenses": {"unexpected": "dict"},
                "documents": {"unexpected": "dict"},
            },
        }
        text = _build_details_card(company)
        self.assertIn("Учредителей в карточке: 0", text)
        self.assertIn("Руководителей в истории: 0", text)
        self.assertIn("Лицензии/документы: 0/0", text)


class DadataAllFieldsDumpTests(unittest.TestCase):
    def test_build_all_fields_block_contains_nested_paths(self):
        company = {
            "data": {
                "inn": "7707083893",
                "name": {"full_with_opf": "ООО Тест"},
                "phones": [{"value": "+7 900 000-00-00"}],
            }
        }

        text = _build_all_fields_block(company)
        self.assertIn("Все поля DaData", text)
        self.assertIn("name.full_with_opf: ООО Тест", text)
        self.assertIn("phones[0].value: +7 900 000-00-00", text)

    def test_build_all_fields_block_limits_size(self):
        company = {"data": {f"k{i}": i for i in range(10)}}
        text = _build_all_fields_block(company, max_lines=3)
        self.assertIn("… и ещё", text)


if __name__ == "__main__":
    unittest.main()
