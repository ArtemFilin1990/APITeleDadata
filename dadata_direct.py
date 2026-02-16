"""Прямой запрос к DaData findById/party и форматирование ответа."""

from __future__ import annotations

import asyncio
import html
import logging
from datetime import datetime

from cache import TTLCache
from config import DADATA_API_KEY, DADATA_FIND_URL
from http_client import get_session
from party_state import format_company_state

logger = logging.getLogger(__name__)

# Чтобы экономить лимиты DaData: кэш ответов на 30 минут.
_PARTY_CACHE = TTLCache(ttl_seconds=30 * 60, max_items=5000)
_BRANCHES_CACHE = TTLCache(ttl_seconds=30 * 60, max_items=2000)
_DADATA_SEM = asyncio.Semaphore(5)


def _cache_key(
    query: str,
    branch_type: str | None = None,
    kpp: str | None = None,
    entity_type: str | None = None,
    statuses: list[str] | tuple[str, ...] | None = None,
) -> str:
    statuses_key = ",".join(statuses or [])
    return f"{query}:{branch_type or 'ALL'}:{kpp or ''}:{entity_type or ''}:{statuses_key}"


def _normalize_branch_type(branch_type: str | None) -> str | None:
    if branch_type is None:
        return None
    normalized = branch_type.strip().upper()
    if normalized not in {"MAIN", "BRANCH"}:
        raise ValueError("branch_type must be one of: MAIN, BRANCH")
    return normalized


def _normalize_entity_type(entity_type: str | None) -> str | None:
    if entity_type is None:
        return None
    normalized = entity_type.strip().upper()
    if normalized not in {"LEGAL", "INDIVIDUAL"}:
        raise ValueError("type must be one of: LEGAL, INDIVIDUAL")
    return normalized


def _normalize_statuses(statuses: list[str] | tuple[str, ...] | None) -> list[str] | None:
    if statuses is None:
        return None
    allowed = {"ACTIVE", "LIQUIDATING", "LIQUIDATED", "BANKRUPT", "REORGANIZING"}
    normalized: list[str] = []
    for raw in statuses:
        value = raw.strip().upper()
        if value not in allowed:
            raise ValueError(
                "status must contain only: ACTIVE, LIQUIDATING, LIQUIDATED, BANKRUPT, REORGANIZING"
            )
        normalized.append(value)
    return normalized


async def fetch_companies(
    query: str,
    branch_type: str | None = None,
    count: int = 10,
    *,
    kpp: str | None = None,
    entity_type: str | None = None,
    statuses: list[str] | tuple[str, ...] | None = None,
) -> list[dict]:
    """Запрашивает список компаний/филиалов по ИНН/ОГРН через DaData API.

    Поддерживает фильтры DaData findById/party: kpp, type, status.
    """
    normalized_branch_type = _normalize_branch_type(branch_type)
    normalized_type = _normalize_entity_type(entity_type)
    normalized_statuses = _normalize_statuses(statuses)

    cache_key = _cache_key(query, normalized_branch_type, kpp, normalized_type, normalized_statuses)
    cached = _BRANCHES_CACHE.get(cache_key)
    if cached is not None:
        return cached

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Token {DADATA_API_KEY}",
    }
    payload: dict[str, str | int] = {"query": query, "count": max(1, min(count, 300))}
    if normalized_branch_type:
        payload["branch_type"] = normalized_branch_type
    if kpp:
        payload["kpp"] = kpp.strip()

    if normalized_type:
        payload["type"] = normalized_type

    if normalized_statuses:
        payload["status"] = normalized_statuses

    try:
        async with _DADATA_SEM:
            session = get_session()
            async with session.post(DADATA_FIND_URL, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.error("DaData HTTP %s: %s", resp.status, body[:500])
                    return []
                data = await resp.json()
    except Exception as exc:
        logger.exception("Ошибка запроса к DaData: %s", exc)
        return []

    suggestions = data.get("suggestions", []) or []
    _BRANCHES_CACHE.set(cache_key, suggestions)
    return suggestions


async def fetch_company(query: str) -> dict | None:
    """Запрашивает одну компанию по ИНН/ОГРН через DaData API.

    По умолчанию запрашивает только головную организацию (branch_type=MAIN),
    чтобы пользователь сразу получал одну карточку.
    """
    cached = _PARTY_CACHE.get(query)
    if cached is not None:
        return cached

    suggestions = await fetch_companies(query=query, branch_type="MAIN", count=1)
    item = suggestions[0] if suggestions else None
    _PARTY_CACHE.set(query, item)
    return item


async def fetch_branches(query: str, count: int = 10) -> list[dict]:
    """Возвращает филиалы организации по ИНН/ОГРН."""
    return await fetch_companies(query=query, branch_type="BRANCH", count=count)


def _v(val: str | None, default: str = "—") -> str:
    """Вернуть значение или прочерк (безопасно для HTML)."""
    if val is None or str(val).strip() == "":
        return default
    return html.escape(str(val).strip())


def _format_date(timestamp_ms: int | None) -> str | None:
    if not timestamp_ms:
        return None
    try:
        return datetime.fromtimestamp(timestamp_ms / 1000).strftime("%d.%m.%Y")
    except Exception:
        return None


def _format_money(value: int | float | None, year: int | None = None) -> str:
    if value is None:
        return "—"
    if year:
        return f"{value:,.0f} ₽ ({year})".replace(",", " ")
    return f"{value:,.0f} ₽".replace(",", " ")


def _entity_type_label(entity_type: str | None) -> str:
    if entity_type == "INDIVIDUAL":
        return "ИП"
    return "Юридическое лицо"


def format_company_short_card(item: dict) -> str:
    """Короткая карточка для первого экрана менеджеру."""
    d = item.get("data", {})
    name_short = _v(d.get("name", {}).get("short_with_opf") or item.get("value"))
    inn = _v(d.get("inn"))
    ogrn = _v(d.get("ogrn"))
    kpp = _v(d.get("kpp"))

    state = d.get("state", {})
    status = _v(state.get("status"))

    address_obj = d.get("address", {})
    address = _v(address_obj.get("value") or address_obj.get("unrestricted_value"))

    mgmt = d.get("management", {})
    manager_name = _v(mgmt.get("name"))
    manager_post = _v(mgmt.get("post"))

    okved = _v(d.get("okved"))
    employee_count = _v(d.get("employee_count"))

    finance = d.get("finance", {})
    revenue = _format_money(finance.get("revenue"), finance.get("year"))

    return "\n".join(
        [
            f"<b>📋 {name_short}</b>",
            f"<b>ИНН:</b> <code>{inn}</code>  <b>ОГРН:</b> <code>{ogrn}</code>  <b>КПП:</b> <code>{kpp}</code>",
            f"<b>Статус:</b> {status}",
            f"<b>Адрес:</b> {address}",
            f"<b>Руководитель:</b> {manager_name} ({manager_post})",
            f"<b>ОКВЭД:</b> <code>{okved}</code>",
            f"<b>Сотрудники:</b> {employee_count}",
            f"<b>Выручка:</b> {revenue}",
        ]
    )


def format_company_details(item: dict) -> str:
    """Формирует расширенную HTML-карточку компании для Telegram."""
    d = item.get("data", {})
    name_full = _v(d.get("name", {}).get("full_with_opf"))
    name_short = _v(d.get("name", {}).get("short_with_opf"))
    inn = _v(d.get("inn"))
    kpp = _v(d.get("kpp"))
    ogrn = _v(d.get("ogrn"))
    okpo = _v(d.get("okpo"))
    oktmo = _v(d.get("oktmo"))
    okato = _v(d.get("okato"))

    address_obj = d.get("address", {})
    address = _v(address_obj.get("unrestricted_value") or address_obj.get("value"))

    mgmt = d.get("management", {})
    manager_name = _v(mgmt.get("name"))
    manager_post = _v(mgmt.get("post"))

    capital = d.get("capital", {})
    cap_value = capital.get("value")
    cap_type = _v(capital.get("type"), default="")
    capital_str = _format_money(cap_value)
    if cap_value is not None and cap_type:
        capital_str += f" ({cap_type})"

    okved = _v(d.get("okved"))
    okved_type = _v(d.get("okved_type"))

    phones_raw = d.get("phones") or []
    phones = _v(", ".join(p.get("value", "") for p in phones_raw if p.get("value")), default="—")
    emails_raw = d.get("emails") or []
    emails = _v(", ".join(e.get("value", "") for e in emails_raw if e.get("value")), default="—")

    entity_type = d.get("type")
    state = d.get("state", {})
    status = _v(format_company_state(state, entity_type))

    reg_date = _format_date(state.get("registration_date")) or "—"
    liq_date = _format_date(state.get("liquidation_date"))

    branch_type = d.get("branch_type")
    branch_count = d.get("branch_count")
    if branch_type == "MAIN" and branch_count:
        branches_str = f"Головная организация, филиалов: {branch_count}"
    elif branch_type == "BRANCH":
        branches_str = "Филиал"
    else:
        branches_str = "—"

    type_label = _entity_type_label(entity_type)

    lines = [
        f"<b>📋 {name_short}</b>",
        "",
        f"<b>Полное наименование:</b> {name_full}",
        f"<b>Тип:</b> {type_label}",
        f"<b>Статус:</b> {status}",
        f"<b>Дата регистрации:</b> {reg_date}",
    ]
    if liq_date:
        lines.append(f"<b>Дата ликвидации:</b> {liq_date}")

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
        f"{_v(branches_str)}",
    ]

    return "\n".join(lines)


def format_company_requisites(item: dict) -> str:
    """Текст для копирования реквизитов в CRM."""
    d = item.get("data", {})
    name_full = _v(d.get("name", {}).get("full_with_opf"))
    inn = _v(d.get("inn"))
    kpp = _v(d.get("kpp"))
    ogrn = _v(d.get("ogrn"))
    address = _v((d.get("address") or {}).get("unrestricted_value"))

    return "\n".join(
        [
            "Реквизиты контрагента:",
            f"Наименование: {name_full}",
            f"ИНН: {inn}",
            f"КПП: {kpp}",
            f"ОГРН: {ogrn}",
            f"Юридический адрес: {address}",
        ]
    )


def format_branches_list(items: list[dict]) -> str:
    """Список филиалов в компактном виде."""
    if not items:
        return "Филиалы не найдены."

    lines = ["<b>🏢 Филиалы</b>"]
    for idx, item in enumerate(items, start=1):
        d = item.get("data", {})
        name = _v(d.get("name", {}).get("short_with_opf") or item.get("value"))
        kpp = _v(d.get("kpp"))
        address = _v((d.get("address") or {}).get("value"))
        lines.append(f"{idx}. {name}")
        lines.append(f"   КПП: <code>{kpp}</code>")
        lines.append(f"   Адрес: {address}")

    return "\n".join(lines)
