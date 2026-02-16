"""Общий HTTP-клиент (aiohttp) для всего приложения.

Зачем:
- не создавать ClientSession на каждый запрос (это дорого и иногда приводит к ResourceWarning);
- централизованно управлять таймаутами/коннектором/закрытием.

Использование:
    from http_client import get_session
    session = get_session()
"""

from __future__ import annotations

import aiohttp
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_session: Optional[aiohttp.ClientSession] = None

DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=15)


def init_session() -> None:
    global _session
    if _session and not _session.closed:
        return

    # Ограничиваем количество одновременных соединений, чтобы не убивать сеть/DaData
    connector = aiohttp.TCPConnector(limit=20, ttl_dns_cache=300)
    _session = aiohttp.ClientSession(timeout=DEFAULT_TIMEOUT, connector=connector)
    logger.info("aiohttp session initialized")


def get_session() -> aiohttp.ClientSession:
    global _session
    if _session is None or _session.closed:
        init_session()
    assert _session is not None
    return _session


async def close_session() -> None:
    global _session
    if _session and not _session.closed:
        await _session.close()
        logger.info("aiohttp session closed")
    _session = None
