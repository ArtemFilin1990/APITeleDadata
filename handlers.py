"""Обработчики команд и сообщений бота."""

import logging

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from dadata_direct import (
    fetch_branches,
    fetch_company,
    format_branches_list,
    format_company_details,
    format_company_requisites,
    format_company_short_card,
)
from dadata_mcp import fetch_company_via_mcp
from keyboards import (
    CB_BACK,
    CB_MODE_DIRECT,
    CB_MODE_MCP,
    CB_PARTY_BRANCHES,
    CB_PARTY_DETAILS,
    CB_PARTY_EXPORT,
    back_menu_kb,
    main_menu_kb,
    party_card_kb,
)
from validators import parse_inns, validate_inn

logger = logging.getLogger(__name__)
router = Router()

WELCOME_TEXT = (
    "<b>Проверка компаний по ИНН/ОГРН</b>\n\n"
    "Выберите режим работы:\n\n"
    "🔍 <b>DaData напрямую</b> — прямой запрос к API DaData, "
    "карточка + кнопки «подробнее / филиалы / экспорт».\n\n"
    "🤖 <b>DaData через AI (MCP)</b> — нейросеть анализирует компанию "
    "через MCP-сервер DaData и выдаёт человекочитаемый отчёт."
)


class CheckINN(StatesGroup):
    waiting_inn_direct = State()
    waiting_inn_mcp = State()


def _extract_query_from_callback(data: str, prefix: str) -> str | None:
    expected = f"{prefix}:"
    if not data.startswith(expected):
        return None
    value = data[len(expected):]
    valid, _ = validate_inn(value)
    return value if valid else None


async def _send_long_message(message: Message, text: str, parse_mode: str = "HTML") -> None:
    if len(text) <= 4000:
        await message.answer(text, parse_mode=parse_mode)
        return

    parts = [text[i: i + 4000] for i in range(0, len(text), 4000)]
    for part in parts:
        await message.answer(part, parse_mode=parse_mode)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb(), parse_mode="HTML")


@router.callback_query(F.data == CB_MODE_DIRECT)
async def on_mode_direct(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CheckINN.waiting_inn_direct)
    await callback.message.edit_text(
        "🔍 <b>Режим: DaData напрямую</b>\n\n"
        "Введите ИНН/ОГРН (10/12 цифр — ИНН, 13/15 — ОГРН).\n"
        "Можно отправить несколько значений, каждый с новой строки.",
        parse_mode="HTML",
        reply_markup=back_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == CB_MODE_MCP)
async def on_mode_mcp(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CheckINN.waiting_inn_mcp)
    await callback.message.edit_text(
        "🤖 <b>Режим: DaData через AI (MCP)</b>\n\n"
        "Введите ИНН/ОГРН (10/12 цифр — ИНН, 13/15 — ОГРН).\n"
        "Можно отправить несколько значений, каждый с новой строки.",
        parse_mode="HTML",
        reply_markup=back_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == CB_BACK)
async def on_back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        WELCOME_TEXT,
        parse_mode="HTML",
        reply_markup=main_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(f"{CB_PARTY_DETAILS}:"))
async def on_party_details(callback: CallbackQuery):
    query = _extract_query_from_callback(callback.data or "", CB_PARTY_DETAILS)
    if not query:
        await callback.answer("Некорректный идентификатор", show_alert=True)
        return

    company = await fetch_company(query)
    if not company:
        await callback.answer("Карточка устарела, запросите снова", show_alert=True)
        return

    await callback.message.answer(format_company_details(company), parse_mode="HTML", reply_markup=back_menu_kb())
    await callback.answer()


@router.callback_query(F.data.startswith(f"{CB_PARTY_EXPORT}:"))
async def on_party_export(callback: CallbackQuery):
    query = _extract_query_from_callback(callback.data or "", CB_PARTY_EXPORT)
    if not query:
        await callback.answer("Некорректный идентификатор", show_alert=True)
        return

    company = await fetch_company(query)
    if not company:
        await callback.answer("Карточка устарела, запросите снова", show_alert=True)
        return

    await callback.message.answer(format_company_requisites(company), parse_mode="HTML", reply_markup=back_menu_kb())
    await callback.answer("Реквизиты готовы")


@router.callback_query(F.data.startswith(f"{CB_PARTY_BRANCHES}:"))
async def on_party_branches(callback: CallbackQuery):
    query = _extract_query_from_callback(callback.data or "", CB_PARTY_BRANCHES)
    if not query:
        await callback.answer("Некорректный идентификатор", show_alert=True)
        return

    branches = await fetch_branches(query)
    await _send_long_message(callback.message, format_branches_list(branches), parse_mode="HTML")
    await callback.answer()


@router.message(CheckINN.waiting_inn_direct)
async def handle_inn_direct(message: Message):
    tokens = parse_inns(message.text or "")
    if not tokens:
        await message.answer(
            "⚠️ Не удалось распознать идентификатор. Введите ИНН/ОГРН в цифрах.",
            reply_markup=back_menu_kb(),
        )
        return

    for token in tokens:
        valid, desc = validate_inn(token)
        if not valid:
            await message.answer(
                f"⚠️ <code>{token}</code> — {desc}",
                parse_mode="HTML",
                reply_markup=back_menu_kb(),
            )
            continue

        wait_msg = await message.answer(
            f"⏳ Запрашиваю данные по идентификатору <code>{token}</code> ({desc})…",
            parse_mode="HTML",
        )

        company = await fetch_company(token)
        if company is None:
            await wait_msg.edit_text(
                f"❌ По значению <code>{token}</code> данные не найдены.",
                parse_mode="HTML",
                reply_markup=back_menu_kb(),
            )
            continue

        data = company.get("data", {})
        has_branches = bool(data.get("branch_count"))

        await wait_msg.edit_text(
            format_company_short_card(company),
            parse_mode="HTML",
            reply_markup=party_card_kb(token, has_branches=has_branches),
        )

    await message.answer(
        "Введите ещё ИНН/ОГРН или вернитесь в меню.",
        reply_markup=back_menu_kb(),
    )


@router.message(CheckINN.waiting_inn_mcp)
async def handle_inn_mcp(message: Message):
    tokens = parse_inns(message.text or "")
    if not tokens:
        await message.answer(
            "⚠️ Не удалось распознать идентификатор. Введите ИНН/ОГРН в цифрах.",
            reply_markup=back_menu_kb(),
        )
        return

    for token in tokens:
        valid, desc = validate_inn(token)
        if not valid:
            await message.answer(
                f"⚠️ <code>{token}</code> — {desc}",
                parse_mode="HTML",
                reply_markup=back_menu_kb(),
            )
            continue

        wait_msg = await message.answer(
            f"⏳ AI анализирует идентификатор <code>{token}</code> ({desc})… Это может занять 10–30 сек.",
            parse_mode="HTML",
        )

        result = await fetch_company_via_mcp(token)

        if len(result) > 4000:
            parts = [result[i: i + 4000] for i in range(0, len(result), 4000)]
            for i, part in enumerate(parts):
                if i == 0:
                    try:
                        await wait_msg.edit_text(part, parse_mode="Markdown")
                    except Exception:
                        await wait_msg.edit_text(part)
                else:
                    try:
                        await message.answer(part, parse_mode="Markdown")
                    except Exception:
                        await message.answer(part)
        else:
            try:
                await wait_msg.edit_text(result, parse_mode="Markdown")
            except Exception:
                await wait_msg.edit_text(result)

    await message.answer(
        "Введите ещё ИНН/ОГРН или вернитесь в меню.",
        reply_markup=back_menu_kb(),
    )
