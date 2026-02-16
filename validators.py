"""Валидация ИНН."""

import re


def validate_inn(inn: str) -> tuple[bool, str]:
    """Проверяет ИНН формата 10/12 цифр."""
    inn = inn.strip()
    if not re.fullmatch(r"\d+", inn):
        return False, "ИНН должен содержать только цифры"

    value_type = {
        10: "ИНН (юр. лицо)",
        12: "ИНН (ИП)",
    }.get(len(inn))
    if value_type:
        return True, value_type

    return False, f"ИНН должен содержать 10 или 12 цифр, получено {len(inn)}"


def parse_inns(text: str) -> list[str]:
    """Извлекает токены из текста (совместимость со старыми тестами/утилитами)."""
    tokens = re.split(r"[\s,;]+", text.strip())
    return [t.strip() for t in tokens if t.strip()]
