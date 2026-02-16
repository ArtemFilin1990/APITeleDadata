"""Клавиатуры бота: reply-меню и inline-навигация."""

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

# Reply menu labels
BTN_START = "🏁 Старт"
BTN_HELLO = "👋 Привет"
BTN_CHECK_INN = "🔎 Проверить ИНН"

# Navigation callback_data (единый стандарт)
CB_NAV_HOME = "nav:home"
CB_NAV_BACK = "nav:back"

CB_PAGE_CARD = "page:card"
CB_PAGE_FINANCE = "page:finance"
CB_PAGE_CASES = "page:cases"
CB_PAGE_DEBTS = "page:debts"
CB_PAGE_INSPECTIONS = "page:inspections"
CB_PAGE_CONTRACTS = "page:contracts"

CB_PAGE_SUCCESSOR = "page:successor"
CB_PAGE_CONTACTS = "page:contacts"
CB_PAGE_AUTHORITIES = "page:authorities"
CB_PAGE_FOUNDERS = "page:founders"
CB_PAGE_TAXES = "page:taxes"

CB_PAGE_FEDRESURS = "page:fedresurs"
CB_PAGE_EFRSB = "page:efrsb"

CB_ACT_NEW_INN = "act:new_inn"
CB_ACT_MENU = "act:menu"
CB_ACT_PDF = "act:pdf"


def reply_main_menu_kb() -> ReplyKeyboardMarkup:
    """Постоянное меню внизу чата."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_START), KeyboardButton(text=BTN_HELLO)],
            [KeyboardButton(text=BTN_CHECK_INN)],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def inline_actions_kb() -> InlineKeyboardMarkup:
    """Фиксированное inline-меню под карточкой и дочерними экранами."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Правопреемник", callback_data=CB_PAGE_SUCCESSOR),
                InlineKeyboardButton(text="Все контакты", callback_data=CB_PAGE_CONTACTS),
                InlineKeyboardButton(text="ФНС/ПФР/ФСС/Росстат", callback_data=CB_PAGE_AUTHORITIES),
                InlineKeyboardButton(text="Новый ИНН", callback_data=CB_ACT_NEW_INN),
                InlineKeyboardButton(text="Меню", callback_data=CB_ACT_MENU),
            ],
            [
                InlineKeyboardButton(text="Финансы", callback_data=CB_PAGE_FINANCE),
                InlineKeyboardButton(text="Суды", callback_data=CB_PAGE_CASES),
                InlineKeyboardButton(text="Правопреемник", callback_data=CB_PAGE_SUCCESSOR),
                InlineKeyboardButton(text="Учредители", callback_data=CB_PAGE_FOUNDERS),
                InlineKeyboardButton(text="Госзакупки", callback_data=CB_PAGE_CONTRACTS),
                InlineKeyboardButton(text="Налоги", callback_data=CB_PAGE_TAXES),
                InlineKeyboardButton(text="Долги", callback_data=CB_PAGE_DEBTS),
            ],
            [
                InlineKeyboardButton(text="Проверки", callback_data=CB_PAGE_INSPECTIONS),
                InlineKeyboardButton(text="Федресурс", callback_data=CB_PAGE_FEDRESURS),
                InlineKeyboardButton(text="ЕФРСБ", callback_data=CB_PAGE_EFRSB),
                InlineKeyboardButton(text="сохранить в pdf", callback_data=CB_ACT_PDF),
            ],
            [
                InlineKeyboardButton(text="назад", callback_data=CB_NAV_BACK),
                InlineKeyboardButton(text="домой", callback_data=CB_NAV_HOME),
            ],
        ]
    )
