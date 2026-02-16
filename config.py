"""Конфигурация бота: загрузка переменных окружения.

Правило:
- Секреты ТОЛЬКО в .env / ENV.
- Обязательные для старта: TELEGRAM_BOT_TOKEN, DADATA_API_KEY.
- Для MCP-режима дополнительно нужны: DADATA_SECRET_KEY, OPENAI_API_KEY.
"""

from __future__ import annotations

import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

# ── Secrets / Keys ───────────────────────────────────────────────────────────

TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
DADATA_API_KEY: str = os.getenv("DADATA_API_KEY", "").strip()
DADATA_SECRET_KEY: str = os.getenv("DADATA_SECRET_KEY", "").strip()
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip()

# ── Validation (hard) ────────────────────────────────────────────────────────
_required = {
    "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
    "DADATA_API_KEY": DADATA_API_KEY,
}
_missing = [k for k, v in _required.items() if not v]
if _missing:
    logging.error("Не заданы переменные окружения: %s", ", ".join(_missing))
    sys.exit(1)

# ── DaData endpoints ─────────────────────────────────────────────────────────

DADATA_FIND_URL = os.getenv(
    "DADATA_FIND_URL",
    "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party",
).strip()

# ── OpenAI ──────────────────────────────────────────────────────────────────

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip()

# ── MCP DaData ──────────────────────────────────────────────────────────────

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "https://mcp.dadata.ru/mcp").strip()

# ── Logging ─────────────────────────────────────────────────────────────────

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").strip()
