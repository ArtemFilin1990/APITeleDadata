"""Валидация идентификаторов организаций (ИНН/ОГРН)."""

import re


def validate_inn(inn: str) -> tuple[bool, str]:
    """Проверяет ИНН/ОГРН для совместимости с существующими вызовами.

    Returns:
        (is_valid, description) — описание формата идентификатора или текст ошибки.
    """
    inn = inn.strip()
    if not re.fullmatch(r"\d+", inn):
        return False, "Идентификатор должен содержать только цифры"

    value_type = {
        10: "ИНН (юр. лицо)",
        12: "ИНН (ИП)",
        13: "ОГРН (юр. лицо)",
        15: "ОГРНИП (ИП)",
    }.get(len(inn))
    if value_type:
        return True, value_type

    return (
        False,
        "Идентификатор должен содержать 10/12 цифр (ИНН) или 13/15 цифр (ОГРН), "
        f"получено {len(inn)}",
    )


def parse_inns(text: str) -> list[str]:
    """Извлекает идентификаторы из текста (по одному на строку или через пробел/запятую)."""
    tokens = re.split(r"[\s,;]+", text.strip())
    return [t.strip() for t in tokens if t.strip()]
