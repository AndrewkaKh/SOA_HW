from __future__ import annotations

import asyncpg


class PostgresClient:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        self._pool = await asyncpg.create_pool(dsn=self._dsn, min_size=1, max_size=5)

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def execute(self, query: str, *args) -> str:
        assert self._pool is not None
        return await self._pool.execute(query, *args)

    async def fetch(self, query: str, *args):
        assert self._pool is not None
        return await self._pool.fetch(query, *args)

    async def fetchval(self, query: str, *args):
        assert self._pool is not None
        return await self._pool.fetchval(query, *args)

    async def executemany(self, query: str, args) -> None:
        assert self._pool is not None
        await self._pool.executemany(query, args)
