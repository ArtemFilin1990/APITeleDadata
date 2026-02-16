"""Запрос к DaData через MCP-сервер (OpenAI Responses API).

Критично:
- Никаких ключей в коде — только через .env / переменные окружения.
- MCP-режим требует: DADATA_API_KEY + DADATA_SECRET_KEY + OPENAI_API_KEY.
"""

from __future__ import annotations

import asyncio
import logging

from cache import TTLCache
from config import (
    DADATA_API_KEY,
    DADATA_SECRET_KEY,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    MCP_SERVER_URL,
)

logger = logging.getLogger(__name__)

# MCP дорогой — кэшируем краткосрочно.
_MCP_CACHE = TTLCache(ttl_seconds=2 * 60 * 60, max_items=2000)
# Ограничиваем параллельные MCP запросы (экономим лимиты/очереди).
_MCP_SEM = asyncio.Semaphore(2)


def _missing_keys_message() -> str:
    missing = []
    if not DADATA_API_KEY:
        missing.append("DADATA_API_KEY")
    if not DADATA_SECRET_KEY:
        missing.append("DADATA_SECRET_KEY")
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    if not missing:
        return ""
    return "❌ Не заданы ключи для MCP-режима: " + ", ".join(missing)


def _extract_text(response) -> str:
    # openai>=1.30 обычно даёт response.output_text
    text = getattr(response, "output_text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()

    # fallback: пробуем собрать вручную
    out = []
    try:
        for item in getattr(response, "output", []) or []:
            content = getattr(item, "content", None)
            if not content:
                continue
            for block in content:
                t = getattr(block, "text", None)
                if t:
                    out.append(t)
    except Exception:
        pass

    joined = "".join(out).strip()
    return joined or str(getattr(response, "output", response))


async def fetch_company_via_mcp(inn: str) -> str:
    """Проверка компании через DaData MCP + OpenAI.

    Возвращает готовый текст для отправки пользователю.
    """
    msg = _missing_keys_message()
    if msg:
        return msg

    cached = _MCP_CACHE.get(inn)
    if cached is not None:
        return cached

    tools = [{
        "type": "mcp",
        "server_label": "dadata",
        "server_url": MCP_SERVER_URL,
        "headers": {
            # DaData MCP: Bearer <api_key>:<secret_key>
            "authorization": f"Bearer {DADATA_API_KEY}:{DADATA_SECRET_KEY}",
        },
        "require_approval": "never",
    }]

    prompt = (
        "Проверь контрагента по ИНН {inn}. "
        "Дай краткий вывод (риск/норма) и затем факты: статус, регистрация/ликвидация, адрес, руководство, ОКВЭД, капитал, филиалы, контакты. "
        "Не выдумывай: если данных нет — пиши 'нет данных'."
    ).format(inn=inn)

    try:
        async with _MCP_SEM:
            # Предпочтительно async-клиент. Если его нет — уходим в to_thread с sync-клиентом.
            try:
                from openai import AsyncOpenAI  # type: ignore
                client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
                response = await client.responses.create(
                    model=OPENAI_MODEL,
                    tools=tools,
                    input=prompt,
                )
            except Exception:
                from openai import OpenAI  # type: ignore
                client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
                response = await asyncio.to_thread(
                    client.responses.create,
                    model=OPENAI_MODEL,
                    tools=tools,
                    input=prompt,
                )

            text = _extract_text(response)
            _MCP_CACHE.set(inn, text)
            return text

    except Exception as e:
        logger.exception("MCP error for INN %s", inn)
        return f"❌ Ошибка MCP-запроса: {e}"
