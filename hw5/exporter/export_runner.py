from __future__ import annotations

import json
import logging
from datetime import date
from time import perf_counter

from postgres_client import PostgresClient
from s3_client import S3Client

logger = logging.getLogger(__name__)


class ExportRunner:
    def __init__(self, postgres: PostgresClient, s3_client: S3Client, bucket: str) -> None:
        self._postgres = postgres
        self._s3_client = s3_client
        self._bucket = bucket

    async def run_for_date(self, metric_date: date) -> dict[str, object]:
        started = perf_counter()
        metrics_rows = await self._postgres.fetch(
            """
            SELECT metric_name, metric_value, computed_at
            FROM metrics
            WHERE metric_date = $1
            ORDER BY metric_name
            """,
            metric_date,
        )
        retention_rows = await self._postgres.fetch(
            """
            SELECT cohort_date, day_of_life, cohort_size, returning_users, retention_pct, computed_at
            FROM retention_cohorts
            WHERE cohort_date = $1
            ORDER BY day_of_life
            """,
            metric_date,
        )

        payload = {
            "metric_date": metric_date.isoformat(),
            "metrics": {
                row["metric_name"]: {
                    "value": row["metric_value"],
                    "computed_at": row["computed_at"].isoformat(),
                }
                for row in metrics_rows
            },
            "retention": [
                {
                    "cohort_date": row["cohort_date"].isoformat(),
                    "day_of_life": row["day_of_life"],
                    "cohort_size": row["cohort_size"],
                    "returning_users": row["returning_users"],
                    "retention_pct": row["retention_pct"],
                    "computed_at": row["computed_at"].isoformat(),
                }
                for row in retention_rows
            ],
        }

        key = f"daily/{metric_date.isoformat()}/aggregates.json"
        await self._s3_client.put_object(self._bucket, key, json.dumps(payload, ensure_ascii=True, indent=2))

        elapsed = perf_counter() - started
        logger.info(
            "Export finished for %s in %.2fs with %s metrics and %s retention rows",
            metric_date.isoformat(),
            elapsed,
            len(metrics_rows),
            len(retention_rows),
        )
        return {
            "metric_date": metric_date.isoformat(),
            "bucket": self._bucket,
            "key": key,
            "metrics_count": len(metrics_rows),
            "retention_count": len(retention_rows),
            "elapsed_seconds": round(elapsed, 3),
        }
