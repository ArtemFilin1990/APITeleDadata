"""Альтернативная точка входа на pyTelegramBotAPI (TeleBot polling)."""

from __future__ import annotations

import asyncio
import logging
import sys

import telebot

from config import LOG_LEVEL, TELEGRAM_BOT_TOKEN
from dadata_direct import fetch_company, format_company_short_card
from http_client import close_session
from validators import validate_inn

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
    BOT.reply_to(message, "Привет 😊\nВведите ИНН (10 или 12 цифр) — соберу карточку компании.")


@BOT.message_handler(func=lambda message: bool(message.text))
def handle_inn(message) -> None:
    text = message.text.strip()
    is_valid, validation_msg = validate_inn(text)
    if not is_valid:
        BOT.reply_to(message, f"❌ {validation_msg}")
        return

    BOT.send_chat_action(message.chat.id, "typing")
    try:
        company = _run_async(fetch_company(text))
    except Exception:
        logging.exception("Ошибка обработки ИНН")
        BOT.reply_to(message, "⚠️ Не удалось получить данные. Попробуйте позже.")
        return

    if not company:
        BOT.reply_to(message, "По этому ИНН/ОГРН данные не найдены.")
        return

    BOT.reply_to(message, format_company_short_card(company))


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
