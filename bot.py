"""Точка входа: запуск Telegram-бота для проверки компаний по ИНН."""

import asyncio
import logging
import sys
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramNetworkError
from aiogram.fsm.storage.memory import MemoryStorage

from config import (
    BOT_STARTUP_MAX_RETRIES,
    BOT_STARTUP_RETRY_BASE_DELAY_SECONDS,
    BOT_STARTUP_RETRY_MAX_DELAY_SECONDS,
    HEALTH_ENABLED,
    HEALTH_HOST,
    LOG_LEVEL,
    PORT,
    TELEGRAM_BOT_TOKEN,
)
from handlers import router
from http_client import close_session


@dataclass
class ServiceStatus:
    ready: bool = False
    started_at: datetime | None = None


SERVICE_STATUS = ServiceStatus()


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


async def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    retries_left = BOT_STARTUP_MAX_RETRIES
    attempt = 1
    health_runner: web.AppRunner | None = None

    if HEALTH_ENABLED:
        health_runner = await _start_health_server(logger)

    logger.info("Бот запускается…")
    try:
        while True:
            bot = Bot(
                token=TELEGRAM_BOT_TOKEN,
                default=DefaultBotProperties(parse_mode="HTML"),
            )
            dp = Dispatcher(storage=MemoryStorage())
            dp.include_router(router)
            SERVICE_STATUS.ready = True
            SERVICE_STATUS.started_at = datetime.now(timezone.utc)

            try:
                await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
                return
            except TelegramNetworkError as exc:
                SERVICE_STATUS.ready = False
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
    finally:
        if health_runner is not None:
            with suppress(Exception):
                await health_runner.cleanup()


async def _start_health_server(logger: logging.Logger) -> web.AppRunner:
    app = web.Application()
    app.router.add_get("/healthz", _healthz)
    app.router.add_get("/readyz", _readyz)
    app.router.add_get("/", _healthz)

    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    site = web.TCPSite(runner, host=HEALTH_HOST, port=PORT)
    await site.start()
    logger.info("HTTP health endpoint started at http://%s:%s", HEALTH_HOST, PORT)
    return runner


def _request_id(request: web.Request) -> str:
    header_request_id = request.headers.get("X-Request-Id", "").strip()
    return header_request_id or str(uuid4())


async def _healthz(request: web.Request) -> web.Response:
    request_id = _request_id(request)
    payload = {
        "status": "ok",
        "service": "inn-checker-bot",
        "request_id": request_id,
    }
    return web.json_response(payload)


async def _readyz(request: web.Request) -> web.Response:
    request_id = _request_id(request)
    status_code = 200 if SERVICE_STATUS.ready else 503
    payload = {
        "status": "ready" if SERVICE_STATUS.ready else "starting",
        "service": "inn-checker-bot",
        "started_at": SERVICE_STATUS.started_at.isoformat() if SERVICE_STATUS.started_at else None,
        "request_id": request_id,
    }
    return web.json_response(payload, status=status_code)


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
