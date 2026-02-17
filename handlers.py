"""Обработчики команд, reply-меню и inline-навигации бота."""

import html
import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from dadata_direct import fetch_company
from keyboards import (
    BTN_CHECK_INN,
    CB_ACT_CRM,
    CB_ACT_EXPORT,
    CB_ACT_MENU,
    CB_ACT_NEW_INN,
    CB_NAV_BACK,
    CB_NAV_HOME,
    CB_PAGE_AUTHORITIES,
    CB_PAGE_CASES,
    CB_PAGE_CONTACTS,
    CB_PAGE_CONTRACTS,
    CB_PAGE_DEBTS,
    CB_PAGE_DETAILS,
    CB_PAGE_EFRSB,
    CB_PAGE_FEDRESURS,
    CB_PAGE_FINANCE,
    CB_PAGE_FOUNDERS,
    CB_PAGE_INSPECTIONS,
    CB_PAGE_MANAGEMENT,
    CB_PAGE_SUCCESSOR,
    CB_PAGE_TAXES,
    CB_PAGE_DOCUMENTS,
    inline_actions_kb,
    reply_main_menu_kb,
)
from validators import parse_inns, validate_company_id

logger = logging.getLogger(__name__)
router = Router()

START_TEXT = (
    "🕵️ Агент на связи. Работаем тихо и без лишнего шума.\n"
    "Только легальные данные из официальных источников.\n\n"
    "🤫 Шёпотом: введи ИНН/ОГРН."
)
HELP_TEXT = (
    "Команды:\n"
    "/start — приветствие\n"
    "/help — это сообщение\n"
    "/find — ввести ИНН/ОГРН для проверки\n\n"
    "Также можно нажать кнопку «🔎 Проверить ИНН»."
)
ASK_INN_TEXT = "Введите ИНН/ОГРН: 10/12 (ИНН) или 13/15 (ОГРН) цифр.\nПример: 3525405517"
ERR_DIGITS_TEXT = "Упс 🙂 Нужны только цифры без пробелов. Попробуйте ещё раз."
ERR_LEN_TEXT = "ИНН/ОГРН должен быть 10/12/13/15 цифр. Пример: 3525405517"
TELEGRAM_TEXT_LIMIT = 4096


class CheckINN(StatesGroup):
    waiting_inn = State()


def _split_for_telegram(text: str, chunk_size: int = TELEGRAM_TEXT_LIMIT) -> list[str]:
    """Разбивает длинный текст на безопасные для Telegram части."""
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    remaining = text
    while len(remaining) > chunk_size:
        split_at = remaining.rfind("\n", 0, chunk_size + 1)
        if split_at <= 0:
            split_at = chunk_size
        chunk = remaining[:split_at].rstrip()
        if not chunk:
            chunk = remaining[:chunk_size]
            split_at = chunk_size
        chunks.append(chunk)
        remaining = remaining[split_at:].lstrip("\n")

    if remaining:
        chunks.append(remaining)
    return chunks


async def _send_text_chunks(message: Message, text: str, *, reply_markup=None) -> None:
    parts = _split_for_telegram(text)
    for index, part in enumerate(parts):
        await message.answer(part, reply_markup=reply_markup if index == 0 else None)


async def _edit_text_chunks(message: Message, text: str, *, reply_markup=None) -> None:
    parts = _split_for_telegram(text)
    await message.edit_text(parts[0], reply_markup=reply_markup)
    for part in parts[1:]:
        await message.answer(part)


def _build_result_totals(found: int, not_found: int, invalid: list[str]) -> str:
    lines = [f"Итог: найдено {found}, не найдено {not_found}."]
    if invalid:
        digits_error = [value for value in invalid if not value.isdigit()]
        length_error = [value for value in invalid if value.isdigit()]
        invalid_chunks = []
        if digits_error:
            invalid_chunks.append(f"не только цифры: {', '.join(digits_error)}")
        if length_error:
            invalid_chunks.append(f"неверная длина: {', '.join(length_error)}")
        lines.append("Невалидные значения: " + "; ".join(invalid_chunks))
    return "\n".join(lines)


def _v(value: str | int | float | None, default: str = "—") -> str:
    if value is None:
        return default
    raw = str(value).strip()
    return html.escape(raw) if raw else default


def _date_from_ms(value: int | None) -> str:
    if not value:
        return "—"
    try:
        return datetime.fromtimestamp(value / 1000).strftime("%d.%m.%Y")
    except Exception:
        return "—"


def _money(value: int | float | str | None) -> str:
    if value is None:
        return "—"
    if isinstance(value, str):
        raw = value.strip().replace(" ", "")
        if not raw:
            return "—"
        raw = raw.replace(",", ".")
    else:
        raw = value

    try:
        amount = float(raw)
    except (TypeError, ValueError):
        # Безопасный fallback, если API вернуло нечисловое значение.
        return _v(str(value))

    return f"{amount:,.0f} ₽".replace(",", " ")


def _d(company: dict) -> dict:
    return company.get("data", {}) if isinstance(company, dict) else {}


def _build_main_card(company: dict) -> str:
    d = _d(company)
    name = d.get("name", {}) or {}
    state = d.get("state", {}) or {}
    management = d.get("management", {}) or {}
    finance = d.get("finance", {}) or {}
    address = d.get("address", {}) or {}

    short_name = _v(name.get("short_with_opf") or company.get("value"))
    reg_date = _date_from_ms(state.get("registration_date"))
    inn = _v(d.get("inn"))
    kpp = _v(d.get("kpp"))
    ogrn = _v(d.get("ogrn"))
    manager_post = _v(management.get("post"), default="руководитель")
    manager_name = _v(management.get("name"))

    employees = _v(d.get("employee_count"))
    fin_year = finance.get("year")
    avg_salary = _money(finance.get("salary"))
    status = _v(state.get("status"))

    addr = _v(address.get("value"))
    okved = _v(d.get("okved"))

    year_suffix = f" ({fin_year})" if fin_year else ""

    return "\n".join(
        [
            "Карточка компании ✅",
            f"🏢 {short_name}",
            f"🆔 ИНН: {inn} • КПП: {kpp}",
            f"🧾 ОГРН: {ogrn}",
            f"📅 Регистрация: {reg_date}",
            f"📍 Адрес: {addr}",
            f"👤 {manager_post}: {manager_name}",
            f"📌 Статус: {status}",
            f"🏷️ ОКВЭД: {okved}",
            f"👥 Штат: {employees}{year_suffix} • 💵 Ср. зарплата: {avg_salary}{year_suffix}",
        ]
    )




def _normalize_dump_value(value: object) -> str:
    if isinstance(value, (dict, list)):
        return "[структура]"
    if value is None:
        return "—"
    return _v(str(value))


def _iter_data_paths(value: object, prefix: str = ""):
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                continue
            child_prefix = f"{prefix}.{key}" if prefix else key
            yield from _iter_data_paths(child, child_prefix)
        return

    if isinstance(value, list):
        if not value:
            yield prefix, "[]"
            return
        for idx, child in enumerate(value):
            child_prefix = f"{prefix}[{idx}]"
            yield from _iter_data_paths(child, child_prefix)
        return

    yield prefix, _normalize_dump_value(value)


def _build_all_fields_block(company: dict, max_lines: int = 200) -> str:
    d = _d(company)
    if not isinstance(d, dict) or not d:
        return "Все поля DaData: нет данных."

    lines = ["Все поля DaData (что вернул тариф):"]
    total = 0
    for path, value in _iter_data_paths(d):
        if not path:
            continue
        total += 1
        if total > max_lines:
            lines.append(f"… и ещё {total - max_lines} полей.")
            break
        lines.append(f"• {path}: {value}")

    if total == 0:
        lines.append("• нет непустых полей")
    return "\n".join(lines)
def _build_details_card(company: dict) -> str:
    d = _d(company)
    name = d.get("name", {}) or {}
    state = d.get("state", {}) or {}
    capital = d.get("capital", {}) or {}
    management = d.get("management", {}) or {}
    finance = d.get("finance", {}) or {}
    address = d.get("address", {}) or {}

    short_name = _v(name.get("short_with_opf") or company.get("value"))
    full_name = _v(name.get("full_with_opf"))
    reg_date = _date_from_ms(state.get("registration_date"))
    inn = _v(d.get("inn"))
    kpp = _v(d.get("kpp"))
    ogrn = _v(d.get("ogrn"))
    ogrn_date = _date_from_ms(d.get("ogrn_date"))
    manager_post = _v(management.get("post"), default="руководитель")
    manager_date = _date_from_ms(management.get("start_date"))
    manager_name = _v(management.get("name"))

    employees = _v(d.get("employee_count"))
    fin_year = finance.get("year")
    avg_salary = _money(finance.get("salary"))
    status = _v(state.get("status"))

    successor = d.get("successors") or []
    successor_name = _v(successor[0].get("value")) if successor and isinstance(successor[0], dict) else "—"

    addr = _v(address.get("unrestricted_value") or address.get("value"))

    okved = _v(d.get("okved"))
    okveds = d.get("okveds") or []
    okved_name = "—"
    if okveds and isinstance(okveds[0], dict):
        okved_name = _v(okveds[0].get("name"))
    okved_count = str(len(okveds)) if isinstance(okveds, list) and okveds else "1"

    tax = d.get("authorities", {}).get("fts_registration") if isinstance(d.get("authorities"), dict) else {}
    tax_name = _v((tax or {}).get("name"))
    tax_date = _date_from_ms((tax or {}).get("date"))

    codes = (
        f"ОКПО {_v(d.get('okpo'))} • ОКАТО {_v(d.get('okato'))} • ОКТМО {_v(d.get('oktmo'))} • "
        f"ОКФС {_v(d.get('okfs'))} • ОКОГУ {_v(d.get('okogu'))} • ОКОПФ {_v(d.get('okopf'))}"
    )

    phones = [p.get("value") for p in (d.get("phones") or []) if isinstance(p, dict) and p.get("value")]
    emails = [e.get("value") for e in (d.get("emails") or []) if isinstance(e, dict) and e.get("value")]
    websites = [w.get("value") for w in (d.get("websites") or []) if isinstance(w, dict) and w.get("value")]

    phones_line = ", ".join(phones[:2]) + (" (+ ещё)" if len(phones) > 2 else "") if phones else "—"
    emails_line = ", ".join(emails[:2]) + (" (+ ещё)" if len(emails) > 2 else "") if emails else "—"
    site_line = websites[0] if websites else "—"

    year_suffix = f" ({fin_year})" if fin_year else ""

    founders = d.get("founders") if isinstance(d.get("founders"), list) else []
    managers = d.get("managers") if isinstance(d.get("managers"), list) else []
    licenses = d.get("licenses") if isinstance(d.get("licenses"), list) else []
    documents = d.get("documents") if isinstance(d.get("documents"), list) else []

    return "\n".join(
        [
            "Подробнее 📄",
            f"🏢 {short_name} (полное: {full_name})",
            f"📅 Регистрация: {reg_date}",
            f"🆔 ИНН/КПП: {inn} / {kpp}",
            f"🧾 ОГРН: {ogrn} от {ogrn_date}",
            f"💰 Уставный капитал: {_money(capital.get('value'))}",
            f"👤 {manager_post} с {manager_date}: {manager_name}",
            f"👥 Штат: {employees}{year_suffix} • 💵 Ср. зарплата: {avg_salary}{year_suffix}",
            f"❌️ Статус: {status}",
            f"✅️Правопреемник: {successor_name}",
            f"👥 Учредителей в карточке: {len(founders)}",
            f"🧑‍💼 Руководителей в истории: {len(managers)}",
            f"📜 Лицензии/документы: {len(licenses)}/{len(documents)}",
            "📍 Юридический адрес",
            f"{addr}",
            "🏷️ Деятельность",
            f"Основной ОКВЭД: {okved} — {okved_name} (всего видов: {okved_count})",
            "🏛️ Налоговый орган",
            f"{tax_name} (с {tax_date})",
            "📌 Коды статистики",
            codes,
            "📞 Контакты",
            f"Тел.: {_v(phones_line)}",
            f"Email: {_v(emails_line)}",
            f"Сайт: {_v(site_line)}",
            "",
            _build_all_fields_block(company),
        ]
    )


def _build_export_text(company: dict) -> str:
    d = _d(company)
    name = d.get("name", {}) or {}
    management = d.get("management", {}) or {}
    address = d.get("address", {}) or {}
    return "\n".join(
        [
            "Экспорт реквизитов 📤",
            f"Наименование: {_v(name.get('full_with_opf') or company.get('value'))}",
            f"ИНН: {_v(d.get('inn'))}",
            f"КПП: {_v(d.get('kpp'))}",
            f"ОГРН: {_v(d.get('ogrn'))}",
            f"Адрес: {_v(address.get('unrestricted_value') or address.get('value'))}",
            f"Руководитель: {_v(management.get('name'))}",
        ]
    )


def _build_crm_text(company: dict) -> str:
    d = _d(company)
    name = d.get("name", {}) or {}
    management = d.get("management", {}) or {}
    address = d.get("address", {}) or {}
    return "\n".join(
        [
            "CRM-блок 🧩",
            f"company_name={_v(name.get('full_with_opf') or company.get('value'))}",
            f"inn={_v(d.get('inn'))}",
            f"kpp={_v(d.get('kpp'))}",
            f"ogrn={_v(d.get('ogrn'))}",
            f"manager={_v(management.get('name'))}",
            f"address={_v(address.get('unrestricted_value') or address.get('value'))}",
        ]
    )


def _full_contacts(company: dict) -> str:
    d = _d(company)
    phones = sorted({p.get("value") for p in (d.get("phones") or []) if isinstance(p, dict) and p.get("value")})
    emails = sorted({e.get("value") for e in (d.get("emails") or []) if isinstance(e, dict) and e.get("value")})
    websites = sorted({w.get("value") for w in (d.get("websites") or []) if isinstance(w, dict) and w.get("value")})

    lines = ["📞 Все контакты"]
    lines.append("Тел.: " + (", ".join(phones) if phones else "—"))
    lines.append("Email: " + (", ".join(emails) if emails else "—"))
    lines.append("Сайт: " + (", ".join(websites) if websites else "—"))
    return "\n".join(lines)


def _format_people(items: list[dict], *, with_share: bool = False) -> str:
    if not items:
        return "данные не предоставлены"

    lines: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        person_name = _v(item.get("name") or item.get("fio") or item.get("value"))
        if person_name == "—":
            continue
        role = _v(item.get("post"), default="")
        share_text = ""
        if with_share:
            share_obj = item.get("share") if isinstance(item.get("share"), dict) else {}
            share_type = _v(share_obj.get("type"), default="")
            share_value = share_obj.get("value")
            if share_value is not None:
                share_text = f" — доля: {_money(share_value)}"
                if share_type:
                    share_text += f" ({share_type})"
        if role:
            lines.append(f"- {person_name} ({role}){share_text}")
        else:
            lines.append(f"- {person_name}{share_text}")

    return "\n".join(lines) if lines else "данные не предоставлены"


def _format_documents(company: dict) -> str:
    d = _d(company)
    documents = d.get("documents") if isinstance(d.get("documents"), list) else []
    licenses = d.get("licenses") if isinstance(d.get("licenses"), list) else []

    lines = ["📜 Лицензии и документы"]

    if licenses:
        lines.append(f"Лицензии: {len(licenses)}")
        for item in licenses[:5]:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"- {_v(item.get('series'))} {_v(item.get('number'))}, выдана {_date_from_ms(item.get('issue_date'))}"
            )
        if len(licenses) > 5:
            lines.append(f"… и ещё {len(licenses) - 5}")
    else:
        lines.append("Лицензии: данные не предоставлены")

    if documents:
        lines.append("")
        lines.append(f"Документы: {len(documents)}")
        for item in documents[:5]:
            if not isinstance(item, dict):
                continue
            lines.append(f"- {_v(item.get('type'))} № {_v(item.get('number'))} от {_date_from_ms(item.get('issue_date'))}")
        if len(documents) > 5:
            lines.append(f"… и ещё {len(documents) - 5}")
    else:
        lines.append("")
        lines.append("Документы: данные не предоставлены")

    return "\n".join(lines)


def _format_page(company: dict, page: str) -> str:
    d = _d(company)
    finance = d.get("finance", {}) or {}
    if page == CB_PAGE_FINANCE:
        year = finance.get("year") or "—"
        revenue = _money(finance.get("revenue"))
        profit = _money(finance.get("profit"))
        return "\n".join(
            [
                f"📊 Финансы ({year})",
                f"💰 Выручка: {revenue}",
                f"📉 Прибыль: {profit}",
                f"🏢 Стоимость: {_money(finance.get('value'))}",
                "",
                "📈 Динамика выручки:",
                "данные не предоставлены",
            ]
        )

    if page == CB_PAGE_CASES:
        return "\n".join([
            "⚖️ Суды (арбитраж)",
            "Дел всего: 0 • Активных: 0",
            "Сумма исков: —",
            "",
            "Последние дела:",
            "данные не предоставлены",
        ])

    if page == CB_PAGE_DEBTS:
        return "\n".join([
            "💼 Исполнительные производства (ФССП)",
            "Производств: 0",
            "Сумма: — • Остаток: —",
            "",
            "Последние:",
            "данные не предоставлены",
        ])

    if page == CB_PAGE_INSPECTIONS:
        return "\n".join([
            "🧾 Проверки",
            "Всего: 0",
            "",
            "Последние:",
            "данные не предоставлены",
        ])

    if page == CB_PAGE_CONTRACTS:
        return "\n".join([
            "📑 Госзакупки",
            "Контрактов: 0 • Сумма: —",
            "",
            "Последние:",
            "данные не предоставлены",
        ])

    if page == CB_PAGE_FEDRESURS:
        return "\n".join([
            "🧩 Федресурс",
            "Событий: 0",
            "Последние:",
            "данные не предоставлены",
        ])

    if page == CB_PAGE_EFRSB:
        return "\n".join([
            "🧩 ЕФРСБ",
            "Событий: 0",
            "Последние:",
            "данные не предоставлены",
        ])

    if page == CB_PAGE_AUTHORITIES:
        auth = d.get("authorities", {}) if isinstance(d.get("authorities"), dict) else {}
        return "\n".join([
            "🏛️ ФНС/ПФР/ФСС/Росстат",
            f"ФНС: {_v((auth.get('fts_registration') or {}).get('name'))}",
            f"ПФР: {_v((auth.get('pf') or {}).get('name'))}",
            f"ФСС: {_v((auth.get('sif') or {}).get('name'))}",
            f"Росстат: {_v((auth.get('rosstat') or {}).get('name'))}",
        ])

    if page == CB_PAGE_FOUNDERS:
        founders = d.get("founders") if isinstance(d.get("founders"), list) else []
        return "\n".join(["👥 Учредители", _format_people(founders, with_share=True)])

    if page == CB_PAGE_MANAGEMENT:
        managers = d.get("managers") if isinstance(d.get("managers"), list) else []
        management = d.get("management") if isinstance(d.get("management"), dict) else {}
        lines = ["🧑‍💼 Руководство"]
        if management:
            lines.append(
                f"Текущий руководитель: {_v(management.get('post'), default='руководитель')} — {_v(management.get('name'))}"
            )
            lines.append(f"С {_date_from_ms(management.get('start_date'))}")
            lines.append("")
        lines.append("История руководителей:")
        lines.append(_format_people(managers))
        return "\n".join(lines)

    if page == CB_PAGE_TAXES:
        auth = d.get("authorities", {}) if isinstance(d.get("authorities"), dict) else {}
        fts = auth.get("fts_registration") if isinstance(auth.get("fts_registration"), dict) else {}
        debts = d.get("fns_debt") if isinstance(d.get("fns_debt"), dict) else {}
        tax_system = d.get("tax_system") if isinstance(d.get("tax_system"), dict) else {}
        return "\n".join(
            [
                "🧾 Налогообложение",
                f"Налоговый орган: {_v(fts.get('name'))}",
                f"Постановка на учёт: {_date_from_ms(fts.get('date'))}",
                f"Система налогообложения: {_v(tax_system.get('name') or tax_system.get('code'))}",
                f"Недоимка/пени/штрафы: {_money(debts.get('debt'))}",
            ]
        )

    if page == CB_PAGE_DOCUMENTS:
        return _format_documents(company)

    if page == CB_PAGE_SUCCESSOR:
        succ = d.get("successors") or []
        if succ and isinstance(succ[0], dict):
            succ_text = "\n".join(f"- {_v(item.get('value'))}" for item in succ if isinstance(item, dict))
        else:
            succ_text = "данные не предоставлены"
        return "\n".join(["✅️Правопреемник", succ_text])

    if page == CB_PAGE_CONTACTS:
        return _full_contacts(company)

    if page == CB_PAGE_DETAILS:
        return _build_details_card(company)

    return _build_main_card(company)


async def _go_input_inn(message: Message, state: FSMContext) -> None:
    await state.set_state(CheckINN.waiting_inn)
    await message.answer(ASK_INN_TEXT, reply_markup=reply_main_menu_kb())


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(START_TEXT, reply_markup=reply_main_menu_kb())


@router.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(HELP_TEXT, reply_markup=reply_main_menu_kb())


@router.message(Command("find"))
async def cmd_find(message: Message, state: FSMContext):
    await _go_input_inn(message, state)


@router.message(F.text == BTN_CHECK_INN)
async def cmd_check_inn(message: Message, state: FSMContext):
    await _go_input_inn(message, state)


@router.message(CheckINN.waiting_inn)
@router.message(F.text)
async def handle_inn(message: Message, state: FSMContext):
    text = (message.text or "").strip()

    if text == BTN_CHECK_INN:
        return

    values = parse_inns(text)
    if not values:
        await message.answer(ERR_LEN_TEXT, reply_markup=reply_main_menu_kb())
        return

    invalid_values = [value for value in values if not validate_company_id(value)[0]]
    valid_values = [value for value in values if value not in invalid_values]
    if not valid_values:
        has_non_digit = any(not value.isdigit() for value in invalid_values)
        await message.answer(
            ERR_DIGITS_TEXT if has_non_digit else ERR_LEN_TEXT,
            reply_markup=reply_main_menu_kb(),
        )
        return

    wait_msg = await message.answer("Ищу данные…", reply_markup=reply_main_menu_kb())

    found_companies: list[tuple[str, dict]] = []
    not_found = 0
    for value in valid_values:
        company = await fetch_company(value)
        if company is None:
            not_found += 1
            continue
        found_companies.append((value, company))

    if not found_companies:
        summary = _build_result_totals(found=0, not_found=not_found, invalid=invalid_values)
        await _edit_text_chunks(
            wait_msg,
            "По указанным ИНН/ОГРН данные не найдены.\n" + summary,
            reply_markup=inline_actions_kb(),
        )
        return

    first_value, first_company = found_companies[0]
    summary = _build_result_totals(found=len(found_companies), not_found=not_found, invalid=invalid_values)

    await state.update_data(
        current_inn=first_value,
        current_company=first_company,
        current_page="page:card",
        history=[],
    )

    await _edit_text_chunks(
        wait_msg,
        f"{_build_main_card(first_company)}\n\n{summary}",
        reply_markup=inline_actions_kb(),
    )


@router.callback_query(F.data == CB_NAV_HOME)
async def on_home(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    company = data.get("current_company")
    if not company:
        await callback.answer("Сначала введите ИНН", show_alert=True)
        return

    await state.update_data(current_page="page:card")
    await _edit_text_chunks(callback.message, _build_main_card(company), reply_markup=inline_actions_kb())
    await callback.answer()


@router.callback_query(F.data == CB_NAV_BACK)
async def on_back(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    company = data.get("current_company")
    if not company:
        await callback.answer("Сначала введите ИНН", show_alert=True)
        return

    history = data.get("history") or []
    if history:
        target_page = history.pop()
        await state.update_data(history=history, current_page=target_page)
        await _edit_text_chunks(callback.message, _format_page(company, target_page), reply_markup=inline_actions_kb())
    else:
        await state.update_data(current_page="page:card")
        await _edit_text_chunks(callback.message, _build_main_card(company), reply_markup=inline_actions_kb())

    await callback.answer()


@router.callback_query(F.data == CB_ACT_NEW_INN)
async def on_new_inn(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(CheckINN.waiting_inn)
    await callback.message.answer(ASK_INN_TEXT, reply_markup=reply_main_menu_kb())
    await callback.answer()


@router.callback_query(F.data == CB_ACT_MENU)
async def on_menu(callback: CallbackQuery):
    await callback.message.answer("Меню показано ниже 👇", reply_markup=reply_main_menu_kb())
    await callback.answer()


@router.callback_query(F.data == CB_ACT_EXPORT)
async def on_export(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    company = data.get("current_company")
    if not company:
        await callback.answer("Сначала введите ИНН", show_alert=True)
        return

    await _send_text_chunks(callback.message, _build_export_text(company), reply_markup=inline_actions_kb())
    await callback.answer("Экспорт подготовлен")


@router.callback_query(F.data == CB_ACT_CRM)
async def on_crm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    company = data.get("current_company")
    if not company:
        await callback.answer("Сначала введите ИНН", show_alert=True)
        return

    await _send_text_chunks(callback.message, _build_crm_text(company), reply_markup=inline_actions_kb())
    await callback.answer("Блок для CRM готов")


@router.callback_query(
    F.data.in_(
        {
            CB_PAGE_FINANCE,
            CB_PAGE_CASES,
            CB_PAGE_DEBTS,
            CB_PAGE_INSPECTIONS,
            CB_PAGE_CONTRACTS,
            CB_PAGE_SUCCESSOR,
            CB_PAGE_CONTACTS,
            CB_PAGE_AUTHORITIES,
            CB_PAGE_FOUNDERS,
            CB_PAGE_MANAGEMENT,
            CB_PAGE_TAXES,
            CB_PAGE_DOCUMENTS,
            CB_PAGE_FEDRESURS,
            CB_PAGE_EFRSB,
            CB_PAGE_DETAILS,
        }
    )
)
async def on_page(callback: CallbackQuery, state: FSMContext):
    page = callback.data or ""
    data = await state.get_data()
    company = data.get("current_company")
    if not company:
        await callback.answer("Сначала введите ИНН", show_alert=True)
        return

    current_page = data.get("current_page", "page:card")
    history = data.get("history") or []
    history.append(current_page)
    await state.update_data(history=history, current_page=page)

    await _edit_text_chunks(callback.message, _format_page(company, page), reply_markup=inline_actions_kb())
    await callback.answer()
