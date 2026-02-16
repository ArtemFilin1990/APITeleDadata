"""Конфигурация бота: загрузка переменных окружения."""

import os
import sys
import logging
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
DADATA_API_KEY: str = os.getenv("DADATA_API_KEY", "")
DADATA_SECRET_KEY: str = os.getenv("DADATA_SECRET_KEY", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# Валидация обязательных переменных
_required = {
    "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
    "DADATA_API_KEY": DADATA_API_KEY,
}

_missing = [k for k, v in _required.items() if not v]
if _missing:
    logging.error("Не заданы переменные окружения: %s", ", ".join(_missing))
    sys.exit(1)

# DaData endpoints
DADATA_FIND_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party"

# OpenAI
OPENAI_BASE_URL = "https://api.openai.com/v1"
OPENAI_MODEL = "gpt-4.1-mini"

# MCP DaData
MCP_SERVER_URL = "https://mcp.dadata.ru/mcp"

# Логирование
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
