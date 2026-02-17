"""Точка входа: запуск Telegram-бота для проверки компаний по ИНН."""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramNetworkError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault

from config import (
    BOT_STARTUP_MAX_RETRIES,
    BOT_STARTUP_RETRY_BASE_DELAY_SECONDS,
    BOT_STARTUP_RETRY_MAX_DELAY_SECONDS,
    LOG_LEVEL,
    TELEGRAM_BOT_TOKEN,
)
from handlers import router
from http_client import close_session


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )
    # Приглушаем шумные логгеры
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.WARNING)


async def setup_commands(bot: Bot) -> None:
    """Регистрирует команды меню бота для русской локали."""

    commands = [
        BotCommand(command="start", description="Запуск"),
        BotCommand(command="help", description="Помощь/меню"),
        BotCommand(command="find", description="Найти компанию по ИНН (10/12 цифр)"),
    ]
    await bot.set_my_commands(
        commands=commands,
        scope=BotCommandScopeDefault(),
        language_code="ru",
    )


async def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    retries_left = BOT_STARTUP_MAX_RETRIES
    attempt = 1

    logger.info("Бот запускается…")
    while True:
        bot = Bot(
            token=TELEGRAM_BOT_TOKEN,
            default=DefaultBotProperties(parse_mode="HTML"),
        )
        dp = Dispatcher(storage=MemoryStorage())
        dp.include_router(router)

        try:
            # Если для бота ранее был включён webhook, polling не сможет получать update'ы.
            await bot.delete_webhook(drop_pending_updates=False)
            await setup_commands(bot)
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
            return
        except TelegramNetworkError as exc:
            if retries_left <= 0:
                logger.error("Не удалось подключиться к Telegram API: %s", exc)
                raise

            delay = _backoff_delay_seconds(attempt)
            logger.warning(
                "Временная ошибка сети Telegram (%s). Повтор через %.1f сек. Осталось попыток: %s",
                exc,
                delay,
                retries_left,
            )
            retries_left -= 1
            attempt += 1
            await asyncio.sleep(delay)
        finally:
            await bot.session.close()


def _backoff_delay_seconds(attempt: int) -> float:
    if attempt < 1:
        attempt = 1
    delay = BOT_STARTUP_RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1))
    return min(delay, BOT_STARTUP_RETRY_MAX_DELAY_SECONDS)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        asyncio.run(close_session())
