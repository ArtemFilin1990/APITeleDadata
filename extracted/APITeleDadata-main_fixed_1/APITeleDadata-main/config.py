"""Конфигурация бота: загрузка переменных окружения.

Важно:
- модуль *не должен* завершать процесс при импорте (иначе ломаются тесты/утилиты);
- валидацию обязательных переменных выполняем явным вызовом validate_required() в entrypoint.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# Совместимость по именам переменных:
# - TELEGRAM_BOT_TOKEN / BOT_TOKEN
# - DADATA_API_KEY / DADATA_TOKEN
# - DADATA_SECRET_KEY / DADATA_SECRET
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN", "")
DADATA_API_KEY: str = os.getenv("DADATA_API_KEY") or os.getenv("DADATA_TOKEN", "")
DADATA_SECRET_KEY: str = os.getenv("DADATA_SECRET_KEY") or os.getenv("DADATA_SECRET", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# Режим работы (на текущем этапе используется polling в bot.py).
MODE: str = os.getenv("MODE", "polling").lower()
WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")
PORT: int = int(os.getenv("PORT", "8080"))


def validate_required() -> None:
    """Проверка обязательных переменных окружения.

    Не делаем sys.exit() на импорте: это должно решаться в точке входа.
    """
    required = {
        "TELEGRAM_BOT_TOKEN|BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "DADATA_API_KEY|DADATA_TOKEN": DADATA_API_KEY,
    }
    missing = [k for k, v in required.items() if not (v or "").strip()]
    if missing:
        raise RuntimeError("Не заданы переменные окружения: " + ", ".join(missing))

# DaData endpoints
DADATA_FIND_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party"

# OpenAI
OPENAI_BASE_URL = "https://api.openai.com/v1"
OPENAI_MODEL = "gpt-4.1-mini"

# MCP DaData
MCP_SERVER_URL = "https://mcp.dadata.ru/mcp"

# Логирование
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
