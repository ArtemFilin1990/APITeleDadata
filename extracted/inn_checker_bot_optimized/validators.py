"""Валидация и парсинг ИНН (10/12 цифр) с проверкой контрольных чисел."""

from __future__ import annotations

import re
from typing import List, Tuple


def _calc_ctrl(digits: List[int], weights: List[int]) -> int:
    s = sum(d * w for d, w in zip(digits, weights))
    return (s % 11) % 10


def validate_inn(inn: str) -> Tuple[bool, str]:
    """Проверяет ИНН по формату и контрольным числам.

    Returns:
        (is_valid, description) — описание: 'юр. лицо', 'ИП' или текст ошибки.
    """
    inn = (inn or "").strip()

    if not re.fullmatch(r"\d+", inn):
        return False, "ИНН должен содержать только цифры"

    if len(inn) not in (10, 12):
        return False, f"ИНН должен содержать 10 (юр. лицо) или 12 (ИП) цифр, получено {len(inn)}"

    digits = [int(ch) for ch in inn]

    if len(inn) == 10:
        # Контрольная цифра: 10-я
        ctrl = _calc_ctrl(digits[:9], [2, 4, 10, 3, 5, 9, 4, 6, 8])
        if ctrl != digits[9]:
            return False, "ошибка контрольного числа (юр. лицо)"
        return True, "юр. лицо"

    # 12 цифр: две контрольные (11-я и 12-я)
    ctrl11 = _calc_ctrl(digits[:10], [7, 2, 4, 10, 3, 5, 9, 4, 6, 8])
    if ctrl11 != digits[10]:
        return False, "ошибка контрольного числа (ИП) — 11-я цифра"

    ctrl12 = _calc_ctrl(digits[:11], [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8])
    if ctrl12 != digits[11]:
        return False, "ошибка контрольного числа (ИП) — 12-я цифра"

    return True, "ИП"


def parse_inns(text: str, *, max_items: int = 50) -> List[str]:
    """Извлекает ИНН из текста.

    - Достаёт любые 10/12-значные последовательности цифр.
    - Дедуплицирует, сохраняя порядок.
    - Ограничивает количество (защита от спама).

    Args:
        text: входной текст
        max_items: максимум ИНН за запрос

    Returns:
        список ИНН (строки)
    """
    text = (text or "").strip()
    if not text:
        return []

    matches = re.findall(r"(?<!\d)(\d{10}|\d{12})(?!\d)", text)
    if not matches:
        # fallback на старую механику, если пользователь ввёл с разделителями
        tokens = re.split(r"[\s,;]+", text)
        matches = [t.strip() for t in tokens if t.strip()]

    # Дедуп + фильтр по длине
    out: List[str] = []
    seen = set()
    for m in matches:
        m = m.strip()
        if len(m) not in (10, 12) or not m.isdigit():
            continue
        if m in seen:
            continue
        seen.add(m)
        out.append(m)
        if len(out) >= max_items:
            break

    return out
