import os
import unittest
from unittest.mock import patch

# Чтобы импорт config.py не завершал процесс в тестах
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("DADATA_API_KEY", "test-dadata-api-key")
os.environ.setdefault("DADATA_SECRET_KEY", "test-dadata-secret")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")

import dadata_direct
import dadata_mcp


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
    def __init__(self, response=None, should_raise=False):
        self._response = response
        self._should_raise = should_raise

    def post(self, *args, **kwargs):
        if self._should_raise:
            raise RuntimeError("network-failure")
        return self._response


class _FakeContent:
    def __init__(self, text):
        self.text = text


class _FakeOutputItem:
    def __init__(self, content):
        self.content = content


class _FakeOpenAIResponse:
    def __init__(self, output):
        self.output = output


class _FakeOpenAIClient:
    def __init__(self, response=None, should_raise=False):
        self._response = response
        self._should_raise = should_raise
        self.responses = self

    def create(self, **kwargs):
        if self._should_raise:
            raise RuntimeError("openai-failure")
        return self._response


class DadataDirectErrorHandlingTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        dadata_direct._PARTY_CACHE._data.clear()
        dadata_direct._BRANCHES_CACHE._data.clear()

    async def test_fetch_company_returns_none_on_non_200(self):
        session = _FakeSession(response=_FakeResponse(status=403, text_data="forbidden"))
        with patch("dadata_direct.get_session", return_value=session):
            result = await dadata_direct.fetch_company("7707083893")
        self.assertIsNone(result)

    async def test_fetch_company_returns_none_on_exception(self):
        session = _FakeSession(should_raise=True)
        with patch("dadata_direct.get_session", return_value=session):
            result = await dadata_direct.fetch_company("7707083893")
        self.assertIsNone(result)

    async def test_fetch_company_returns_first_suggestion(self):
        payload = {"suggestions": [{"value": "first"}, {"value": "second"}]}
        session = _FakeSession(response=_FakeResponse(status=200, json_data=payload))
        with patch("dadata_direct.get_session", return_value=session):
            result = await dadata_direct.fetch_company("7707083893")
        self.assertEqual(result, {"value": "first"})


class DadataMcpErrorHandlingTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_company_via_mcp_returns_config_error_when_keys_missing(self):
        with patch("dadata_mcp.OPENAI_API_KEY", ""), patch("dadata_mcp.DADATA_SECRET_KEY", ""):
            result = await dadata_mcp.fetch_company_via_mcp("7707083893")
        self.assertIn("MCP-режим недоступен", result)
        self.assertIn("OPENAI_API_KEY", result)
        self.assertIn("DADATA_SECRET_KEY", result)

    async def test_fetch_company_via_mcp_returns_error_on_openai_exception(self):
        fake_client = _FakeOpenAIClient(should_raise=True)
        with patch("dadata_mcp.OpenAI", return_value=fake_client):
            result = await dadata_mcp.fetch_company_via_mcp("7707083893")
        self.assertIn("Ошибка MCP-запроса", result)
        self.assertIn("openai-failure", result)

    async def test_fetch_company_via_mcp_extracts_text(self):
        response = _FakeOpenAIResponse(
            output=[_FakeOutputItem([_FakeContent("Часть 1 "), _FakeContent("Часть 2")])]
        )
        fake_client = _FakeOpenAIClient(response=response)
        with patch("dadata_mcp.OpenAI", return_value=fake_client):
            result = await dadata_mcp.fetch_company_via_mcp("7707083893")
        self.assertEqual(result, "Часть 1 Часть 2")


if __name__ == "__main__":
    unittest.main()
