"""Валидация ИНН/ОГРН."""

import re


def validate_company_id(value: str) -> tuple[bool, str]:
    """Проверяет идентификатор компании (ИНН или ОГРН)."""
    value = value.strip()
    if not re.fullmatch(r"\d+", value):
        return False, "Идентификатор должен содержать только цифры"

    value_type = {
        10: "ИНН (юр. лицо)",
        12: "ИНН (ИП)",
        13: "ОГРН (юр. лицо)",
        15: "ОГРНИП",
    }.get(len(value))
    if value_type:
        return True, value_type

    return False, (
        "Идентификатор должен содержать 10/12 цифр (ИНН) "
        f"или 13/15 цифр (ОГРН), получено {len(value)}"
    )


def validate_inn(inn: str) -> tuple[bool, str]:
    """Совместимость со старыми вызовами: валидирует ИНН/ОГРН."""
    return validate_company_id(inn)


def parse_inns(text: str) -> list[str]:
    """Извлекает токены из текста (совместимость со старыми тестами/утилитами)."""
    tokens = re.split(r"[\s,;]+", text.strip())
    return [t.strip() for t in tokens if t.strip()]
