from __future__ import annotations

from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from export_runner import ExportRunner


class ExportScheduler:
    def __init__(self, runner: ExportRunner, interval_seconds: int) -> None:
        self._runner = runner
        self._interval_seconds = interval_seconds
        self._scheduler = AsyncIOScheduler()

    async def start(self) -> None:
        await self._runner.run_for_date(date.today())
        self._scheduler.add_job(self._run_for_today, "interval", seconds=self._interval_seconds)
        self._scheduler.start()

    async def stop(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    async def _run_for_today(self) -> None:
        await self._runner.run_for_date(date.today())
