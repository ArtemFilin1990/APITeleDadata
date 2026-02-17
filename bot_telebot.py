"""Альтернативная точка входа на pyTelegramBotAPI (TeleBot polling)."""

from __future__ import annotations

import asyncio
import logging
import sys

import telebot

from config import LOG_LEVEL, TELEGRAM_BOT_TOKEN
from dadata_direct import fetch_company, format_company_short_card
from http_client import close_session
from validators import parse_inns, validate_company_id

BOT = telebot.TeleBot(token=TELEGRAM_BOT_TOKEN, parse_mode="HTML")


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("telebot").setLevel(logging.WARNING)


def _run_async(coro):
    return asyncio.run(coro)


@BOT.message_handler(commands=["start"])
def handle_start(message) -> None:
    BOT.reply_to(
        message,
        "Бесплатный быстрый сервис проверки контрагентов ⚡\n"
        "Только легальные данные из официальных источников.\n\n"
        "Введите ИНН/ОГРН — соберу карточку компании и ключевые риски.",
    )


@BOT.message_handler(func=lambda message: bool(message.text))
def handle_inn(message) -> None:
    values = parse_inns(message.text.strip())
    if not values:
        BOT.reply_to(message, "❌ Введите ИНН/ОГРН: 10/12/13/15 цифр.")
        return

    invalid_values = [value for value in values if not validate_company_id(value)[0]]
    valid_values = [value for value in values if value not in invalid_values]
    if not valid_values:
        BOT.reply_to(message, "❌ Введите ИНН/ОГРН: 10/12/13/15 цифр.")
        return

    BOT.send_chat_action(message.chat.id, "typing")
    first_company = None
    found = 0
    not_found = 0
    for value in valid_values:
        try:
            company = _run_async(fetch_company(value))
        except Exception:
            logging.exception("Ошибка обработки ИНН/ОГРН")
            BOT.reply_to(message, "⚠️ Не удалось получить данные. Попробуйте позже.")
            return

        if not company:
            not_found += 1
            continue

        found += 1
        if first_company is None:
            first_company = company

    if first_company is None:
        BOT.reply_to(message, f"По указанным ИНН/ОГРН данные не найдены.\n\nИтог: найдено 0, не найдено {not_found}.")
        return

    summary = f"\n\nИтог: найдено {found}, не найдено {not_found}."
    if invalid_values:
        summary += f"\nНевалидные значения: {', '.join(invalid_values)}"

    BOT.reply_to(message, format_company_short_card(first_company) + summary)


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Бот запускается (pyTelegramBotAPI)…")
    try:
        BOT.infinity_polling(skip_pending=True)
    finally:
        _run_async(close_session())
        logger.info("Бот остановлен.")


if __name__ == "__main__":
    main()
