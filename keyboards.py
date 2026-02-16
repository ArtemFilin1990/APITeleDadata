"""Инлайн-клавиатуры бота."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Callback data
CB_MODE_DIRECT = "mode_direct"
CB_MODE_MCP = "mode_mcp"
CB_BACK = "back_to_menu"

CB_PARTY_DETAILS = "party:details"
CB_PARTY_BRANCHES = "party:branches"
CB_PARTY_EXPORT = "party:export"


def main_menu_kb() -> InlineKeyboardMarkup:
    """Главное меню выбора режима."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔍 DaData напрямую",
                    callback_data=CB_MODE_DIRECT,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🤖 DaData через AI (MCP)",
                    callback_data=CB_MODE_MCP,
                ),
            ],
        ]
    )


def back_menu_kb() -> InlineKeyboardMarkup:
    """Кнопка «Назад в меню»."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="↩️ Назад в меню",
                    callback_data=CB_BACK,
                ),
            ],
        ]
    )


def party_card_kb(query: str, has_branches: bool) -> InlineKeyboardMarkup:
    """Кнопки для карточки компании.

    query ограничен validate_inn (10/12/13/15 цифр), поэтому безопасно включать в callback_data.
    """
    buttons = [
        [InlineKeyboardButton(text="📄 Подробнее", callback_data=f"{CB_PARTY_DETAILS}:{query}")],
        [InlineKeyboardButton(text="📋 Скопировать реквизиты", callback_data=f"{CB_PARTY_EXPORT}:{query}")],
    ]

    if has_branches:
        buttons.insert(
            1,
            [InlineKeyboardButton(text="🏢 Филиалы", callback_data=f"{CB_PARTY_BRANCHES}:{query}")],
        )

    buttons.append([
        InlineKeyboardButton(text="↩️ Назад в меню", callback_data=CB_BACK),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
