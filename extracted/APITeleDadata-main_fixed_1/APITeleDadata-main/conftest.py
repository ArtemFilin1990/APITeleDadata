"""Pytest bootstrap.

Проект не оформлен как пакет (нет src/ и installable wheel), поэтому при режиме
importlib (pytest>=8) модули из корня могут не находиться.

Добавляем корень репозитория в sys.path, чтобы тесты стабильно импортировали
modules вида `import dadata_direct`.
"""

from __future__ import annotations

import sys
from pathlib import Path
import os


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# В CI/локальных окружениях переменные могут быть определены, но пустые.
# Для тестов поднимаем минимальный набор, не трогая непустые значения.
if not os.environ.get("TELEGRAM_BOT_TOKEN") and not os.environ.get("BOT_TOKEN"):
    os.environ["TELEGRAM_BOT_TOKEN"] = "test-token"
if not os.environ.get("DADATA_API_KEY") and not os.environ.get("DADATA_TOKEN"):
    os.environ["DADATA_API_KEY"] = "test-dadata-api-key"
if not os.environ.get("DADATA_SECRET_KEY") and not os.environ.get("DADATA_SECRET"):
    os.environ["DADATA_SECRET_KEY"] = "test-dadata-secret"
if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "test-openai-key"
