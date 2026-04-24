from __future__ import annotations

import asyncio
from typing import Any

from clickhouse_driver import Client


class ClickHouseClient:
    def __init__(self, host: str, port: int, database: str) -> None:
        self._host = host
        self._port = port
        self._database = database

    def _create_client(self) -> Client:
        return Client(host=self._host, port=self._port, database=self._database)

    def _execute_sync(self, query: str, params: Any = None) -> list[Any]:
        client = self._create_client()
        return client.execute(query, params)

    async def fetch(self, query: str, params: Any = None) -> list[Any]:
        return await asyncio.to_thread(self._execute_sync, query, params)

    async def execute(self, query: str, params: Any = None) -> None:
        await asyncio.to_thread(self._execute_sync, query, params)

    async def insert(self, query: str, rows: list[dict[str, Any]]) -> None:
        await asyncio.to_thread(self._execute_sync, query, rows)
