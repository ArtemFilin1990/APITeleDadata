"""Обработчики команд и сообщений бота."""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards import (
    main_menu_kb,
    back_menu_kb,
    CB_MODE_DIRECT,
    CB_MODE_MCP,
    CB_BACK,
)
from validators import validate_inn, parse_inns
from dadata_direct import fetch_company, format_company_card
from dadata_mcp import fetch_company_via_mcp

logger = logging.getLogger(__name__)
router = Router()

WELCOME_TEXT = (
    "<b>Проверка компаний по ИНН</b>\n\n"
    "Выберите режим работы:\n\n"
    "🔍 <b>DaData напрямую</b> — прямой запрос к API DaData, "
    "структурированная карточка с реквизитами.\n\n"
    "🤖 <b>DaData через AI (MCP)</b> — нейросеть анализирует компанию "
    "через MCP-сервер DaData и выдаёт человекочитаемый отчёт."
)


# ── FSM ──────────────────────────────────────────────────────────────────────

class CheckINN(StatesGroup):
    waiting_inn_direct = State()
    waiting_inn_mcp = State()


# ── /start ───────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb(), parse_mode="HTML")


# ── Выбор режима ─────────────────────────────────────────────────────────────

@router.callback_query(F.data == CB_MODE_DIRECT)
async def on_mode_direct(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CheckINN.waiting_inn_direct)
    await callback.message.edit_text(
        "🔍 <b>Режим: DaData напрямую</b>\n\n"
        "Введите ИНН (10 цифр — юр. лицо, 12 — ИП).\n"
        "Можно отправить несколько ИНН, каждый с новой строки.",
        parse_mode="HTML",
        reply_markup=back_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == CB_MODE_MCP)
async def on_mode_mcp(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CheckINN.waiting_inn_mcp)
    await callback.message.edit_text(
        "🤖 <b>Режим: DaData через AI (MCP)</b>\n\n"
        "Введите ИНН (10 цифр — юр. лицо, 12 — ИП).\n"
        "Можно отправить несколько ИНН, каждый с новой строки.",
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


# ── Обработка ИНН: прямой режим ─────────────────────────────────────────────

@router.message(CheckINN.waiting_inn_direct)
async def handle_inn_direct(message: Message, state: FSMContext):
    tokens = parse_inns(message.text or "")
    if not tokens:
        await message.answer(
            "⚠️ Не удалось распознать ИНН. Введите 10 или 12 цифр.",
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

        wait_msg = await message.answer(f"⏳ Запрашиваю данные по ИНН <code>{token}</code> ({desc})…", parse_mode="HTML")

        company = await fetch_company(token)
        if company is None:
            await wait_msg.edit_text(
                f"❌ По ИНН <code>{token}</code> данные не найдены.",
                parse_mode="HTML",
                reply_markup=back_menu_kb(),
            )
            continue

        card = format_company_card(company)
        # Telegram ограничивает сообщение 4096 символами
        if len(card) > 4000:
            parts = [card[i : i + 4000] for i in range(0, len(card), 4000)]
            for i, part in enumerate(parts):
                if i == 0:
                    await wait_msg.edit_text(part, parse_mode="HTML")
                else:
                    await message.answer(part, parse_mode="HTML")
        else:
            await wait_msg.edit_text(card, parse_mode="HTML")

    await message.answer(
        "Введите ещё ИНН или вернитесь в меню.",
        reply_markup=back_menu_kb(),
    )


# ── Обработка ИНН: MCP-режим ────────────────────────────────────────────────

@router.message(CheckINN.waiting_inn_mcp)
async def handle_inn_mcp(message: Message, state: FSMContext):
    tokens = parse_inns(message.text or "")
    if not tokens:
        await message.answer(
            "⚠️ Не удалось распознать ИНН. Введите 10 или 12 цифр.",
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
            f"⏳ AI анализирует ИНН <code>{token}</code> ({desc})… Это может занять 10–30 сек.",
            parse_mode="HTML",
        )

        result = await fetch_company_via_mcp(token)

        # MCP-ответ — обычный текст (Markdown от AI), отправляем как Markdown
        if len(result) > 4000:
            parts = [result[i : i + 4000] for i in range(0, len(result), 4000)]
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
                # Если Markdown не парсится — отправляем без разметки
                await wait_msg.edit_text(result)

    await message.answer(
        "Введите ещё ИНН или вернитесь в меню.",
        reply_markup=back_menu_kb(),
    )
