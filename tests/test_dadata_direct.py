import os
import unittest
from unittest.mock import patch

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("DADATA_API_KEY", "test-dadata-api-key")

import dadata_direct


class _FakeResponse:
    def __init__(self, status=200, json_data=None, text_data=""):
        self.status = status
        self._json_data = json_data if json_data is not None else {}
        self._text_data = text_data

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def json(self):
        return self._json_data

    async def text(self):
        return self._text_data


class _FakeSession:
    def __init__(self, response=None):
        self._response = response
        self.calls = 0

    def post(self, *args, **kwargs):
        self.calls += 1
        return self._response


class DadataDirectFormattingTests(unittest.TestCase):
    def test_short_card_contains_key_fields(self):
        item = {
            "value": 'ООО "Тест"',
            "data": {
                "name": {"short_with_opf": 'ООО "Тест"'},
                "inn": "7707083893",
                "ogrn": "1027700132195",
                "kpp": "770701001",
                "state": {"status": "ACTIVE"},
                "address": {"value": "г Москва"},
                "management": {"name": "Иванов И.И.", "post": "Директор"},
                "okved": "62.01",
                "employee_count": 10,
                "finance": {"revenue": 1234567, "year": 2023},
            },
        }

        card = dadata_direct.format_company_short_card(item)
        self.assertIn("ООО", card)
        self.assertIn("ИНН", card)
        self.assertIn("Выручка", card)

    def test_requisites_formats_plain_text(self):
        item = {
            "data": {
                "name": {"full_with_opf": 'ООО "Тест"'},
                "inn": "7707083893",
                "kpp": "770701001",
                "ogrn": "1027700132195",
                "address": {"unrestricted_value": "109000, г Москва"},
            }
        }
        reqs = dadata_direct.format_company_requisites(item)
        self.assertIn("Реквизиты контрагента", reqs)
        self.assertIn("109000, г Москва", reqs)

    def test_format_branches_list_empty(self):
        self.assertEqual(dadata_direct.format_branches_list([]), "Филиалы не найдены.")


class DadataDirectCachingTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_company_uses_cache(self):
        dadata_direct._PARTY_CACHE._data.clear()
        dadata_direct._BRANCHES_CACHE._data.clear()

        payload = {"suggestions": [{"value": "first"}]}
        session = _FakeSession(response=_FakeResponse(status=200, json_data=payload))

        with patch("dadata_direct.get_session", return_value=session):
            first = await dadata_direct.fetch_company("7707083893")
            second = await dadata_direct.fetch_company("7707083893")

        self.assertEqual(first, {"value": "first"})
        self.assertEqual(second, {"value": "first"})
        self.assertEqual(session.calls, 1)


    async def test_fetch_companies_handles_non_200(self):
        dadata_direct._BRANCHES_CACHE._data.clear()
        session = _FakeSession(response=_FakeResponse(status=429, text_data="rate limit"))

        with patch("dadata_direct.get_session", return_value=session):
            result = await dadata_direct.fetch_companies("7707083893")

        self.assertEqual(result, [])
        self.assertEqual(session.calls, 1)

    async def test_fetch_companies_uses_cache_for_same_key(self):
        dadata_direct._BRANCHES_CACHE._data.clear()
        payload = {"suggestions": [{"value": "branch"}]}
        session = _FakeSession(response=_FakeResponse(status=200, json_data=payload))

        with patch("dadata_direct.get_session", return_value=session):
            first = await dadata_direct.fetch_companies("7707083893", branch_type="MAIN", count=1)
            second = await dadata_direct.fetch_companies("7707083893", branch_type="MAIN", count=1)

        self.assertEqual(first, [{"value": "branch"}])
        self.assertEqual(second, [{"value": "branch"}])
        self.assertEqual(session.calls, 1)


if __name__ == "__main__":
    unittest.main()
