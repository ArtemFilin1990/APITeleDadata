"""Обработчики команд, reply-меню и inline-навигации бота."""

import html
import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from dadata_direct import fetch_company
from keyboards import (
    BTN_CHECK_INN,
    BTN_HELLO,
    BTN_START,
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
    CB_PAGE_SUCCESSOR,
    CB_PAGE_TAXES,
    inline_actions_kb,
    reply_main_menu_kb,
)
from validators import validate_inn

logger = logging.getLogger(__name__)
router = Router()

START_TEXT = "Привет 😊\nВведите ИНН (10 или 12 цифр) — соберу карточку и риски."
HELLO_TEXT = "Я на месте 🙂\nНажмите «🔎 Проверить ИНН» или просто отправьте ИНН."
RESTART_TEXT = "Начинаем заново.\nВведите ИНН (10 или 12 цифр) — только цифры."
ASK_INN_TEXT = "Введите ИНН: 10 или 12 цифр, без пробелов.\nПример: 3525405517"
ERR_DIGITS_TEXT = "Упс 🙂 Нужны только цифры без пробелов. Попробуйте ещё раз."
ERR_LEN_TEXT = "ИНН должен быть 10 или 12 цифр. Пример: 3525405517"


class CheckINN(StatesGroup):
    waiting_inn = State()


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


def _money(value: int | float | None) -> str:
    if value is None:
        return "—"
    return f"{value:,.0f} ₽".replace(",", " ")


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
        return "\n".join([
            "👥 Учредители",
            "данные не предоставлены",
        ])

    if page == CB_PAGE_TAXES:
        return "\n".join([
            "🧾 Налоги",
            "данные не предоставлены",
        ])

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


@router.message(F.text == BTN_HELLO)
async def cmd_hello(message: Message):
    await message.answer(HELLO_TEXT, reply_markup=reply_main_menu_kb())


@router.message(F.text == BTN_START)
async def cmd_restart(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(RESTART_TEXT, reply_markup=reply_main_menu_kb())


@router.message(F.text == BTN_CHECK_INN)
async def cmd_check_inn(message: Message, state: FSMContext):
    await _go_input_inn(message, state)


@router.message(CheckINN.waiting_inn)
@router.message(F.text)
async def handle_inn(message: Message, state: FSMContext):
    text = (message.text or "").strip()

    if text in {BTN_START, BTN_HELLO, BTN_CHECK_INN}:
        return

    if not text.isdigit():
        await message.answer(ERR_DIGITS_TEXT, reply_markup=reply_main_menu_kb())
        return

    valid, _ = validate_inn(text)
    if not valid:
        await message.answer(ERR_LEN_TEXT, reply_markup=reply_main_menu_kb())
        return

    wait_msg = await message.answer("Ищу данные…", reply_markup=reply_main_menu_kb())
    company = await fetch_company(text)
    if company is None:
        await wait_msg.edit_text(
            "По этому ИНН данные не найдены. Проверьте номер и попробуйте снова.",
            reply_markup=inline_actions_kb(),
        )
        return

    await state.update_data(
        current_inn=text,
        current_company=company,
        current_page="page:card",
        history=[],
    )

    await wait_msg.edit_text(_build_main_card(company), reply_markup=inline_actions_kb())


@router.callback_query(F.data == CB_NAV_HOME)
async def on_home(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    company = data.get("current_company")
    if not company:
        await callback.answer("Сначала введите ИНН", show_alert=True)
        return

    await state.update_data(current_page="page:card")
    await callback.message.edit_text(_build_main_card(company), reply_markup=inline_actions_kb())
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
        await callback.message.edit_text(_format_page(company, target_page), reply_markup=inline_actions_kb())
    else:
        await state.update_data(current_page="page:card")
        await callback.message.edit_text(_build_main_card(company), reply_markup=inline_actions_kb())

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

    await callback.message.answer(_build_export_text(company), reply_markup=inline_actions_kb())
    await callback.answer("Экспорт подготовлен")


@router.callback_query(F.data == CB_ACT_CRM)
async def on_crm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    company = data.get("current_company")
    if not company:
        await callback.answer("Сначала введите ИНН", show_alert=True)
        return

    await callback.message.answer(_build_crm_text(company), reply_markup=inline_actions_kb())
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
            CB_PAGE_TAXES,
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

    await callback.message.edit_text(_format_page(company, page), reply_markup=inline_actions_kb())
    await callback.answer()
