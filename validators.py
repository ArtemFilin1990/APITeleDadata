"""Валидация ИНН."""

import re


def validate_inn(inn: str) -> tuple[bool, str]:
    """Проверяет ИНН.

    Returns:
        (is_valid, description) — описание: 'юр. лицо', 'ИП' или текст ошибки.
    """
    inn = inn.strip()
    if not re.fullmatch(r"\d+", inn):
        return False, "ИНН должен содержать только цифры"
    if len(inn) == 10:
        return True, "юр. лицо"
    if len(inn) == 12:
        return True, "ИП"
    return False, f"ИНН должен содержать 10 (юр. лицо) или 12 (ИП) цифр, получено {len(inn)}"


def parse_inns(text: str) -> list[str]:
    """Извлекает все ИНН из текста (по одному на строку или через пробел/запятую)."""
    tokens = re.split(r"[\s,;]+", text.strip())
    return [t.strip() for t in tokens if t.strip()]
