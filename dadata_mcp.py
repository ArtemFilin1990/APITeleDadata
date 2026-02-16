"""Запрос к DaData через MCP-сервер с использованием OpenAI Responses API."""

import logging

from openai import OpenAI

from config import (
    DADATA_API_KEY,
    DADATA_SECRET_KEY,
    MCP_SERVER_URL,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
)

logger = logging.getLogger(__name__)


def _validate_mcp_config() -> tuple[bool, str]:
    """Проверка обязательных переменных для MCP-режима."""
    missing = []
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    if not DADATA_SECRET_KEY:
        missing.append("DADATA_SECRET_KEY")

    if missing:
        missing_str = ", ".join(missing)
        return False, (
            "❌ MCP-режим недоступен: не заданы переменные окружения "
            f"{missing_str}. Обратитесь к администратору бота."
        )
    return True, ""


def _extract_text_from_response(response) -> str:
    """Извлекает текст из OpenAI Responses API ответа."""
    chunks: list[str] = []
    for item in getattr(response, "output", []):
        for content in getattr(item, "content", []):
            text = getattr(content, "text", None)
            if text:
                chunks.append(text)

    if chunks:
        return "".join(chunks)
    return str(getattr(response, "output", ""))


async def fetch_company_via_mcp(inn: str) -> str:
    """Проверка компании через DaData MCP + OpenAI AI.
    
    Args:
        inn: ИНН компании для проверки
        
    Returns:
        Текстовый ответ от AI или сообщение об ошибке
    """
    config_valid, config_error = _validate_mcp_config()
    if not config_valid:
        logger.warning("MCP mode disabled due to missing configuration")
        return config_error

    try:
        client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

        response = client.responses.create(
            model=OPENAI_MODEL,
            tools=[{
                "type": "mcp",
                "server_label": "dadata",
                "server_url": MCP_SERVER_URL,
                "headers": {
                    "authorization": f"Bearer {DADATA_API_KEY}:{DADATA_SECRET_KEY}"
                },
                "require_approval": "never"
            }],
            input=f"Проверь контрагента по ИНН {inn}. Надёжный ли он? Дай подробный анализ: реквизиты, статус, адрес, руководство, финансы."
        )

        result_text = _extract_text_from_response(response)
        if not result_text:
            return "❌ Не удалось получить ответ от AI."

        return result_text

    except Exception as exc:
        logger.exception("MCP error for INN %s", inn)
        return f"❌ Ошибка MCP-запроса: {exc}"
