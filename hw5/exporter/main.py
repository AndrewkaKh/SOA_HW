from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from config import get_settings
from export_runner import ExportRunner
from postgres_client import PostgresClient
from routes.export import router as export_router
from routes.health import router as health_router
from s3_client import S3Client
from scheduler import ExportScheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    postgres = PostgresClient(
        dsn=(
            f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
            f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
        )
    )
    await postgres.connect()

    s3_client = S3Client(
        endpoint_url=settings.minio_endpoint_url,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        region_name=settings.minio_region,
    )

    runner = ExportRunner(postgres, s3_client, settings.minio_bucket)
    scheduler = ExportScheduler(runner, settings.export_interval_seconds)
    app.state.export_runner = runner
    await scheduler.start()

    try:
        yield
    finally:
        await scheduler.stop()
        await postgres.close()


app = FastAPI(title="movie-exporter", lifespan=lifespan)
app.include_router(health_router)
app.include_router(export_router)
