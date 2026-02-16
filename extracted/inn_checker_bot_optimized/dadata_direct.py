"""Прямой запрос к DaData findById/party и форматирование карточки для Telegram (HTML)."""

from __future__ import annotations

import html
import logging
import asyncio
from datetime import datetime
from typing import Any, Dict, Optional

import aiohttp

from cache import TTLCache
from http_client import get_session
from config import DADATA_API_KEY, DADATA_FIND_URL

logger = logging.getLogger(__name__)

# Кэшируем ответы DaData: экономим время и лимиты.
_DADATA_CACHE = TTLCache(ttl_seconds=6*60*60, max_items=5000)
# Ограничиваем параллельные запросы к DaData.
_DADATA_SEM = asyncio.Semaphore(5)


async def fetch_company(inn: str) -> Optional[Dict[str, Any]]:
    """Запрашивает данные компании по ИНН через DaData API.

    Returns:
        dict с данными компании или None при ошибке / пустом ответе.
    """
    # Сначала пробуем кэш
    cached = _DADATA_CACHE.get(inn)
    if cached is not None:
        return cached

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Token {DADATA_API_KEY}",
    }
    payload = {"query": inn}

    try:
        async with _DADATA_SEM:
            session = get_session()
            async with session.post(
                DADATA_FIND_URL,
                json=payload,
                headers=headers,
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.error("DaData HTTP %s: %s", resp.status, body[:500])
                    return None
                data = await resp.json()
    except Exception as exc:
        logger.exception("Ошибка запроса к DaData: %s", exc)
        return None

        logger.exception("Ошибка запроса к DaData: %s", exc)
        return None

    suggestions = data.get("suggestions", [])
    if not suggestions:
        return None
    result = suggestions[0]
    _DADATA_CACHE.set(inn, result)
    return result


def _v(val: Any, default: str = "—") -> str:
    """Вернуть строковое значение или прочерк."""
    if val is None:
        return default
    s = str(val).strip()
    return s if s else default


def _h(val: Any, default: str = "—") -> str:
    """Экранировать значение для HTML-разметки Telegram."""
    return html.escape(_v(val, default), quote=False)


def _status_label(state: Optional[Dict[str, Any]]) -> str:
    if not state:
        return "—"
    code = state.get("status")
    mapping = {
        "ACTIVE": "✅ Действующая",
        "LIQUIDATING": "⚠️ Ликвидируется",
        "LIQUIDATED": "❌ Ликвидирована",
        "BANKRUPT": "❌ Банкрот",
        "REORGANIZING": "⚠️ Реорганизация",
    }
    return mapping.get(code, code or "—")


def _ts_to_date(ts_ms: Any) -> str:
    if not ts_ms:
        return "—"
    try:
        return datetime.fromtimestamp(float(ts_ms) / 1000).strftime("%d.%m.%Y")
    except Exception:
        return "—"


def format_company_card(item: Dict[str, Any]) -> str:
    """Формирует HTML-карточку компании для Telegram."""
    d = item.get("data", {}) or {}

    name_full = _h((d.get("name", {}) or {}).get("full_with_opf"))
    name_short = _h((d.get("name", {}) or {}).get("short_with_opf"))
    inn = _h(d.get("inn"))
    kpp = _h(d.get("kpp"))
    ogrn = _h(d.get("ogrn"))
    okpo = _h(d.get("okpo"))
    oktmo = _h(d.get("oktmo"))
    okato = _h(d.get("okato"))

    # Адрес
    address_obj = d.get("address", {}) or {}
    address = _h(address_obj.get("unrestricted_value") or address_obj.get("value"))

    # Руководитель
    mgmt = d.get("management", {}) or {}
    manager_name = _h(mgmt.get("name"))
    manager_post = _h(mgmt.get("post"))

    # Уставный капитал
    capital = d.get("capital", {}) or {}
    cap_value = capital.get("value")
    cap_type = capital.get("type")
    if cap_value is not None:
        try:
            capital_str = f"{float(cap_value):,.0f} ₽".replace(",", " ")
        except Exception:
            capital_str = _h(cap_value)
        if cap_type:
            capital_str += f" ({_h(cap_type)})"
    else:
        capital_str = "—"

    # ОКВЭД
    okved = _h(d.get("okved"))
    okved_type = _h(d.get("okved_type"))

    # Контакты
    phones_raw = d.get("phones") or []
    phones = ", ".join(_h(p.get("value", ""), default="") for p in phones_raw if p.get("value")) or "—"
    emails_raw = d.get("emails") or []
    emails = ", ".join(_h(e.get("value", ""), default="") for e in emails_raw if e.get("value")) or "—"

    # Статус
    state = d.get("state", {}) or {}
    status = _status_label(state)
    reg_date = _ts_to_date(state.get("registration_date"))
    liq_date = _ts_to_date(state.get("liquidation_date"))
    liq_date = None if liq_date == "—" else liq_date

    # Филиалы
    branch_type = d.get("branch_type")
    branch_count = d.get("branch_count")
    if branch_type == "MAIN" and branch_count:
        branches_str = _h(f"Головная организация, филиалов: {branch_count}")
    elif branch_type == "BRANCH":
        branches_str = _h("Филиал")
    else:
        branches_str = "—"

    # Тип: юр. лицо / ИП
    entity_type = d.get("type")
    type_label = "ИП" if entity_type == "INDIVIDUAL" else "Юридическое лицо"

    lines = [
        f"<b>📋 {name_short}</b>",
        "",
        f"<b>Полное наименование:</b> {name_full}",
        f"<b>Тип:</b> {html.escape(type_label, quote=False)}",
        f"<b>Статус:</b> {html.escape(status, quote=False)}",
        f"<b>Дата регистрации:</b> {html.escape(reg_date, quote=False)}",
    ]
    if liq_date:
        lines.append(f"<b>Дата ликвидации:</b> {html.escape(liq_date, quote=False)}")

    lines += [
        "",
        "<b>━━━ Реквизиты ━━━</b>",
        f"<b>ИНН:</b> <code>{inn}</code>",
        f"<b>КПП:</b> <code>{kpp}</code>",
        f"<b>ОГРН:</b> <code>{ogrn}</code>",
        f"<b>ОКПО:</b> <code>{okpo}</code>",
        f"<b>ОКТМО:</b> <code>{oktmo}</code>",
        f"<b>ОКАТО:</b> <code>{okato}</code>",
        "",
        "<b>━━━ Адрес ━━━</b>",
        f"{address}",
        "",
        "<b>━━━ Руководство ━━━</b>",
        f"<b>Должность:</b> {manager_post}",
        f"<b>ФИО:</b> {manager_name}",
        "",
        "<b>━━━ Финансы ━━━</b>",
        f"<b>Уставный капитал:</b> {capital_str}",
        "",
        "<b>━━━ Деятельность ━━━</b>",
        f"<b>ОКВЭД:</b> {okved} (версия {okved_type})",
        "",
        "<b>━━━ Контакты ━━━</b>",
        f"<b>Телефоны:</b> {phones}",
        f"<b>Email:</b> {emails}",
        "",
        "<b>━━━ Филиалы ━━━</b>",
        f"{branches_str}",
    ]

    return "\n".join(lines)
