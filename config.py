"""Конфигурация бота: загрузка переменных окружения."""

import logging
import os
import sys

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

# Валидация обязательных переменных
_required = {
    "TELEGRAM_BOT_TOKEN|BOT_TOKEN": TELEGRAM_BOT_TOKEN,
}

_missing = [k for k, v in _required.items() if not v]
if _missing:
    logging.error("Не заданы переменные окружения: %s", ", ".join(_missing))
    sys.exit(1)

if not DADATA_API_KEY:
    logging.warning(
        "Не задан DADATA_API_KEY|DADATA_TOKEN: прямые запросы к DaData будут недоступны до установки переменной окружения."
    )

# DaData endpoints
DADATA_FIND_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party"

# OpenAI
OPENAI_BASE_URL = "https://api.openai.com/v1"
OPENAI_MODEL = "gpt-4.1-mini"

# MCP DaData
MCP_SERVER_URL = "https://mcp.dadata.ru/mcp"

# Логирование
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


def _get_int_env(name: str, default: int, *, minimum: int = 0) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        logging.warning("Некорректное значение %s=%r, используем %s", name, raw, default)
        return default
    if value < minimum:
        logging.warning("Значение %s=%s меньше %s, используем %s", name, value, minimum, default)
        return default
    return value


def _get_float_env(name: str, default: float, *, minimum: float = 0.0) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        logging.warning("Некорректное значение %s=%r, используем %s", name, raw, default)
        return default
    if value < minimum:
        logging.warning("Значение %s=%s меньше %s, используем %s", name, value, minimum, default)
        return default
    return value


# Поведение при временных сетевых ошибках Telegram API.
BOT_STARTUP_MAX_RETRIES = _get_int_env("BOT_STARTUP_MAX_RETRIES", 0, minimum=0)
BOT_STARTUP_RETRY_BASE_DELAY_SECONDS = _get_float_env(
    "BOT_STARTUP_RETRY_BASE_DELAY_SECONDS", 2.0, minimum=0.1
)
BOT_STARTUP_RETRY_MAX_DELAY_SECONDS = _get_float_env(
    "BOT_STARTUP_RETRY_MAX_DELAY_SECONDS", 30.0, minimum=0.1
)

# HTTP health/readiness endpoint для container runtime (Amvera, Kubernetes и т.п.)
HEALTH_HOST = os.getenv("HEALTH_HOST", "0.0.0.0")
PORT = _get_int_env("PORT", 8080, minimum=1)
HEALTH_ENABLED = os.getenv("HEALTH_ENABLED", "1").strip().lower() not in {"0", "false", "no"}
