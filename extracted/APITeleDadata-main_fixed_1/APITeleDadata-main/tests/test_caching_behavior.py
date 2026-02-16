import unittest
from unittest.mock import patch

import dadata_direct


class _FakeResponse:
    def __init__(self, status=200, json_data=None, text_data=""):
        self.status = status
        self._json_data = json_data or {}
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


class CachingBehaviorTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        dadata_direct._PARTY_CACHE._data.clear()
        dadata_direct._BRANCHES_CACHE._data.clear()

    async def test_main_search_caches_in_party_cache(self):
        payload = {"suggestions": [{"value": "main-item"}]}
        session = _FakeSession(response=_FakeResponse(status=200, json_data=payload))
        with patch("dadata_direct.get_session", return_value=session):
            # Выполняем поиск MAIN (count=1)
            suggestions = await dadata_direct.fetch_companies("7707083893", branch_type="MAIN", count=1)
            self.assertEqual(suggestions, [{"value": "main-item"}])

            # Должен быть сохранён одиночный элемент в _PARTY_CACHE под ключом query
            cached = dadata_direct._PARTY_CACHE.get("7707083893")
            self.assertEqual(cached, {"value": "main-item"})

            # Повторный вызов fetch_company должен вернуть значение из кэша и не инкрементировать вызовы сессии
            result = await dadata_direct.fetch_company("7707083893")
            self.assertEqual(result, {"value": "main-item"})
            self.assertEqual(session.calls, 1)

    async def test_branch_search_caches_in_branches_cache(self):
        payload = {"suggestions": [{"value": "branch-1"}]}
        session = _FakeSession(response=_FakeResponse(status=200, json_data=payload))
        with patch("dadata_direct.get_session", return_value=session):
            # Первый вызов fill cache
            first = await dadata_direct.fetch_companies("7707083893", branch_type="BRANCH", count=10)
            self.assertEqual(first, [{"value": "branch-1"}])

            # Повторный вызов должен использовать _BRANCHES_CACHE и не инкрементировать calls
            second = await dadata_direct.fetch_companies("7707083893", branch_type="BRANCH", count=10)
            self.assertEqual(second, [{"value": "branch-1"}])
            self.assertEqual(session.calls, 1)


if __name__ == "__main__":
    unittest.main()