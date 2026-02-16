"""Работа со справочником статусов организаций из party-state.csv."""

from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path

# Источник: https://github.com/hflabs/party-state/blob/master/party-state.csv
PARTY_STATE_CSV_PATH = Path(__file__).resolve().parent / "data" / "party-state.csv"

_STATUS_PRESENTATION = {
    "ACTIVE": "✅ Действующая",
    "LIQUIDATING": "⚠️ Ликвидируется",
    "LIQUIDATED": "❌ Ликвидирована",
    "BANKRUPT": "❌ Банкрот",
    "REORGANIZING": "⚠️ Реорганизация",
}


@lru_cache(maxsize=1)
def _party_state_by_key() -> dict[tuple[str, str, str], str]:
    """Вернуть map ((entity_type, code, status) -> description)."""
    mapping: dict[tuple[str, str, str], str] = {}

    if not PARTY_STATE_CSV_PATH.exists():
        return mapping

    with PARTY_STATE_CSV_PATH.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            code = (row.get("code") or "").strip()
            entity_type = (row.get("type") or "").strip().upper()
            status = (row.get("status") or "").strip().upper()
            description = (row.get("description") or "").strip()
            if not code or not entity_type or not description:
                continue

            # Основной ключ — с учетом статуса из party-state,
            # fallback-ключ (status="") оставляем для обратной совместимости/неполных данных.
            mapping[(entity_type, code, status)] = description
            mapping.setdefault((entity_type, code, ""), description)

    return mapping


def format_company_state(state: dict | None, entity_type: str | None) -> str:
    """Форматировать статус компании, добавляя расшифровку reason code из party-state."""
    if not state:
        return "—"

    status = str(state.get("status") or "").strip().upper()
    base_status = _STATUS_PRESENTATION.get(status, status or "—")

    reason_code = state.get("code")
    if reason_code is None:
        return base_status

    entity_key = "INDIVIDUAL" if entity_type == "INDIVIDUAL" else "LEGAL"
    code_key = str(reason_code).strip()

    party_state = _party_state_by_key()
    reason_desc = (
        party_state.get((entity_key, code_key, status))
        or party_state.get((entity_key, code_key, ""))
    )
    if not reason_desc:
        return base_status

    return f"{base_status} (код {code_key}: {reason_desc})"
