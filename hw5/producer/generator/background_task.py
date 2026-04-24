from __future__ import annotations

import asyncio
import logging

from generator.session_generator import SessionGenerator
from kafka_producer import KafkaEventProducer

logger = logging.getLogger(__name__)


class GeneratorBackgroundTask:
    def __init__(
        self,
        session_generator: SessionGenerator,
        producer: KafkaEventProducer,
        interval_seconds: float,
    ) -> None:
        self._session_generator = session_generator
        self._producer = producer
        self._interval_seconds = interval_seconds
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._run(), name="movie-event-generator")

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            logger.info("Generator task cancelled")
        self._task = None

    async def _run(self) -> None:
        backfill_events = self._session_generator.generate_backfill_events()
        logger.info("Generated %s backfill events", len(backfill_events))
        for event in backfill_events:
            await asyncio.to_thread(
                self._producer.send_with_retry,
                event.to_kafka_dict(),
                event.user_id,
            )

        while True:
            live_events = self._session_generator.generate_live_events()
            logger.info("Generated %s live events", len(live_events))
            for event in live_events:
                await asyncio.to_thread(
                    self._producer.send_with_retry,
                    event.to_kafka_dict(),
                    event.user_id,
                )
            await asyncio.sleep(self._interval_seconds)
