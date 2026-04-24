from __future__ import annotations

import logging
from datetime import date, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from aggregation_runner import AggregationRunner

logger = logging.getLogger(__name__)


class AggregationScheduler:
    def __init__(self, runner: AggregationRunner, interval_seconds: int, bootstrap_days: int) -> None:
        self._runner = runner
        self._interval_seconds = interval_seconds
        self._bootstrap_days = bootstrap_days
        self._scheduler = AsyncIOScheduler()

    async def start(self) -> None:
        await self._bootstrap_recent_days()
        self._scheduler.add_job(self._run_recent_window, "interval", seconds=self._interval_seconds)
        self._scheduler.start()

    async def stop(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    async def _bootstrap_recent_days(self) -> None:
        today = date.today()
        for offset in range(self._bootstrap_days, -1, -1):
            target_date = today - timedelta(days=offset)
            try:
                await self._runner.run_for_date(target_date)
            except Exception:
                logger.exception("Bootstrap aggregation failed for %s", target_date.isoformat())

    async def _run_recent_window(self) -> None:
        await self._bootstrap_recent_days()
