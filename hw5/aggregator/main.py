from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from aggregation_runner import AggregationRunner
from clickhouse_client import ClickHouseClient
from config import get_settings
from postgres_client import PostgresClient
from routes.health import router as health_router
from routes.recalc import router as recalc_router
from scheduler import AggregationScheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    clickhouse = ClickHouseClient(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        database=settings.clickhouse_database,
    )
    postgres = PostgresClient(
        dsn=(
            f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
            f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
        )
    )
    await postgres.connect()

    runner = AggregationRunner(clickhouse, postgres, settings.top_movies_limit)
    scheduler = AggregationScheduler(runner, settings.aggregation_interval_seconds, settings.aggregation_bootstrap_days)

    app.state.aggregation_runner = runner
    await scheduler.start()

    try:
        yield
    finally:
        await scheduler.stop()
        await postgres.close()


app = FastAPI(title="movie-aggregator", lifespan=lifespan)
app.include_router(health_router)
app.include_router(recalc_router)
