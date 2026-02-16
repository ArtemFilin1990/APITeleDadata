"""Прямой запрос к DaData findById/party и форматирование ответа."""

import logging
import aiohttp
from config import DADATA_API_KEY, DADATA_FIND_URL

logger = logging.getLogger(__name__)


async def fetch_company(inn: str) -> dict | None:
    """Запрашивает данные компании по ИНН через DaData API.

    Returns:
        dict с данными компании или None при ошибке / пустом ответе.
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Token {DADATA_API_KEY}",
    }
    payload = {"query": inn}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                DADATA_FIND_URL, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.error("DaData HTTP %s: %s", resp.status, body[:500])
                    return None
                data = await resp.json()
    except Exception as exc:
        logger.exception("Ошибка запроса к DaData: %s", exc)
        return None

    suggestions = data.get("suggestions", [])
    if not suggestions:
        return None
    return suggestions[0]


def _v(val: str | None, default: str = "—") -> str:
    """Вернуть значение или прочерк."""
    if val is None or str(val).strip() == "":
        return default
    return str(val).strip()


def _status_label(state: dict | None) -> str:
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


def format_company_card(item: dict) -> str:
    """Формирует HTML-карточку компании для Telegram."""
    d = item.get("data", {})
    name_full = _v(d.get("name", {}).get("full_with_opf"))
    name_short = _v(d.get("name", {}).get("short_with_opf"))
    inn = _v(d.get("inn"))
    kpp = _v(d.get("kpp"))
    ogrn = _v(d.get("ogrn"))
    okpo = _v(d.get("okpo"))
    oktmo = _v(d.get("oktmo"))
    okato = _v(d.get("okato"))

    # Адрес
    address_obj = d.get("address", {})
    address = _v(address_obj.get("unrestricted_value") or address_obj.get("value"))

    # Руководитель
    mgmt = d.get("management", {})
    manager_name = _v(mgmt.get("name"))
    manager_post = _v(mgmt.get("post"))

    # Уставный капитал
    capital = d.get("capital", {})
    cap_value = capital.get("value")
    cap_type = capital.get("type")
    if cap_value is not None:
        capital_str = f"{cap_value:,.0f} ₽".replace(",", " ")
        if cap_type:
            capital_str += f" ({cap_type})"
    else:
        capital_str = "—"

    # ОКВЭД
    okved = _v(d.get("okved"))
    okved_type = _v(d.get("okved_type"))

    # Контакты
    phones_raw = d.get("phones") or []
    phones = ", ".join(p.get("value", "") for p in phones_raw if p.get("value")) or "—"
    emails_raw = d.get("emails") or []
    emails = ", ".join(e.get("value", "") for e in emails_raw if e.get("value")) or "—"

    # Статус
    state = d.get("state", {})
    status = _status_label(state)
    reg_date = state.get("registration_date")
    if reg_date:
        from datetime import datetime
        try:
            reg_date = datetime.fromtimestamp(reg_date / 1000).strftime("%d.%m.%Y")
        except Exception:
            reg_date = "—"
    else:
        reg_date = "—"

    liq_date = state.get("liquidation_date")
    if liq_date:
        from datetime import datetime
        try:
            liq_date = datetime.fromtimestamp(liq_date / 1000).strftime("%d.%m.%Y")
        except Exception:
            liq_date = None

    # Филиалы
    branch_type = d.get("branch_type")
    branch_count = d.get("branch_count")
    if branch_type == "MAIN" and branch_count:
        branches_str = f"Головная организация, филиалов: {branch_count}"
    elif branch_type == "BRANCH":
        branches_str = "Филиал"
    else:
        branches_str = "—"

    # Тип: юр. лицо / ИП
    entity_type = d.get("type")
    type_label = "ИП" if entity_type == "INDIVIDUAL" else "Юридическое лицо"

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
        f"{branches_str}",
    ]

    return "\n".join(lines)
