from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from config import get_settings
from generator.background_task import GeneratorBackgroundTask
from generator.session_generator import SessionGenerator
from kafka_producer import KafkaEventProducer
from routes.events import router as events_router
from routes.health import router as health_router
from schema_registry import SchemaRegistryRegistrar

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    schema_path = Path(__file__).resolve().parent.parent / "schemas" / "movie_event.avsc"
    registrar = SchemaRegistryRegistrar(settings.schema_registry_url, settings.kafka_topic, schema_path)
    await registrar.register()
    producer = KafkaEventProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        schema_registry_url=settings.schema_registry_url,
        topic=settings.kafka_topic,
        schema_str=registrar.load_schema(),
    )
    app.state.event_producer = producer
    generator_task = None

    if settings.generator_enabled:
        generator = SessionGenerator(backfill_days=settings.generator_backfill_days)
        generator_task = GeneratorBackgroundTask(
            session_generator=generator,
            producer=producer,
            interval_seconds=settings.generator_interval_seconds,
        )
        await generator_task.start()

    app.state.generator_task = generator_task
    try:
        yield
    finally:
        if generator_task is not None:
            await generator_task.stop()
        producer.close()


app = FastAPI(title="movie-producer", lifespan=lifespan)
app.include_router(health_router)
app.include_router(events_router)
