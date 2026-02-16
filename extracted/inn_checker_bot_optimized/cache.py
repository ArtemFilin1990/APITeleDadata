"""Простой TTL-кэш в памяти (без внешних зависимостей).

Цель: не дергать API повторно по одному и тому же ИНН в рамках короткого окна.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


@dataclass
class CacheItem:
    value: Any
    expires_at: float


class TTLCache:
    def __init__(self, ttl_seconds: int = 3600, max_items: int = 2000) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_items = max_items
        self._data: Dict[str, CacheItem] = {}

    def get(self, key: str) -> Optional[Any]:
        item = self._data.get(key)
        if not item:
            return None
        if item.expires_at < time.time():
            self._data.pop(key, None)
            return None
        return item.value

    def set(self, key: str, value: Any) -> None:
        # Простая защита от бесконечного роста: при переполнении удаляем часть протухших/старых.
        if len(self._data) >= self.max_items:
            self._gc()

        self._data[key] = CacheItem(value=value, expires_at=time.time() + self.ttl_seconds)

    def _gc(self) -> None:
        now = time.time()
        # 1) удалить протухшие
        expired = [k for k, v in self._data.items() if v.expires_at < now]
        for k in expired:
            self._data.pop(k, None)

        # 2) если всё ещё слишком много — удалить произвольные (LRU не нужен для задачи)
        if len(self._data) >= self.max_items:
            for k in list(self._data.keys())[: max(1, self.max_items // 10)]:
                self._data.pop(k, None)
