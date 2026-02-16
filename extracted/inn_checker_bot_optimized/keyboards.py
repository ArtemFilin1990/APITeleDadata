"""Инлайн-клавиатуры бота."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Callback data
CB_MODE_DIRECT = "mode_direct"
CB_MODE_MCP = "mode_mcp"
CB_BACK = "back_to_menu"


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
