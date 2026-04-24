from __future__ import annotations

import json
import logging
from datetime import date
from time import perf_counter

from clickhouse_client import ClickHouseClient
from metrics.conversion import calculate_conversion
from metrics.dau import calculate_dau
from metrics.retention import calculate_retention
from metrics.top_movies import calculate_top_movies
from metrics.watch_time import calculate_watch_time
from postgres_client import PostgresClient

logger = logging.getLogger(__name__)


class AggregationRunner:
    def __init__(
        self,
        clickhouse: ClickHouseClient,
        postgres: PostgresClient,
        top_movies_limit: int,
    ) -> None:
        self._clickhouse = clickhouse
        self._postgres = postgres
        self._top_movies_limit = top_movies_limit

    async def run_for_date(self, metric_date: date) -> dict[str, object]:
        started = perf_counter()
        logger.info("Aggregation started for %s", metric_date.isoformat())

        dau = await calculate_dau(self._clickhouse, metric_date)
        avg_watch_time = await calculate_watch_time(self._clickhouse, metric_date)
        top_movies = await calculate_top_movies(self._clickhouse, metric_date, self._top_movies_limit)
        conversion = await calculate_conversion(self._clickhouse, metric_date)
        retention = await calculate_retention(self._clickhouse, metric_date)

        await self._replace_clickhouse_aggregates(metric_date, dau, avg_watch_time, top_movies, conversion, retention)
        await self._upsert_postgres_metrics(metric_date, dau, avg_watch_time, top_movies, conversion, retention)

        elapsed = perf_counter() - started
        written_records = 4 + len(top_movies) + len(retention)
        logger.info(
            "Aggregation finished for %s in %.2fs with %s records",
            metric_date.isoformat(),
            elapsed,
            written_records,
        )
        return {
            "metric_date": metric_date.isoformat(),
            "dau": dau,
            "avg_watch_time": avg_watch_time,
            "top_movies": top_movies,
            "conversion": conversion,
            "retention_rows": len(retention),
            "elapsed_seconds": round(elapsed, 3),
        }

    async def _replace_clickhouse_aggregates(
        self,
        metric_date: date,
        dau: int,
        avg_watch_time: float,
        top_movies: list[dict[str, int | str]],
        conversion: dict[str, float | int],
        retention: list[dict[str, float | int | str]],
    ) -> None:
        await self._clickhouse.execute(
            """
            ALTER TABLE agg_dau DELETE WHERE event_date = %(event_date)s SETTINGS mutations_sync = 2
            """,
            {"event_date": metric_date},
        )
        await self._clickhouse.insert(
            "INSERT INTO agg_dau (event_date, unique_users) VALUES",
            [{"event_date": metric_date, "unique_users": dau}],
        )

        await self._clickhouse.execute(
            """
            ALTER TABLE agg_avg_watch_time DELETE WHERE event_date = %(event_date)s SETTINGS mutations_sync = 2
            """,
            {"event_date": metric_date},
        )
        await self._clickhouse.insert(
            "INSERT INTO agg_avg_watch_time (event_date, avg_progress_seconds) VALUES",
            [{"event_date": metric_date, "avg_progress_seconds": avg_watch_time}],
        )

        await self._clickhouse.execute(
            """
            ALTER TABLE agg_conversion DELETE WHERE event_date = %(event_date)s SETTINGS mutations_sync = 2
            """,
            {"event_date": metric_date},
        )
        await self._clickhouse.insert(
            """
            INSERT INTO agg_conversion
            (event_date, view_started_count, view_finished_count, conversion_ratio)
            VALUES
            """,
            [
                {
                    "event_date": metric_date,
                    "view_started_count": conversion["view_started_count"],
                    "view_finished_count": conversion["view_finished_count"],
                    "conversion_ratio": conversion["conversion_ratio"],
                }
            ],
        )

        await self._clickhouse.execute(
            """
            ALTER TABLE agg_top_movies DELETE WHERE event_date = %(event_date)s SETTINGS mutations_sync = 2
            """,
            {"event_date": metric_date},
        )
        if top_movies:
            await self._clickhouse.insert(
                "INSERT INTO agg_top_movies (event_date, movie_id, view_count, rank) VALUES",
                [{"event_date": metric_date, **row} for row in top_movies],
            )

        await self._clickhouse.execute(
            """
            ALTER TABLE agg_retention DELETE WHERE cohort_date = %(cohort_date)s SETTINGS mutations_sync = 2
            """,
            {"cohort_date": metric_date},
        )
        await self._clickhouse.insert(
            """
            INSERT INTO agg_retention
            (cohort_date, day_of_life, cohort_size, returning_users, retention_pct)
            VALUES
            """,
            retention,
        )

    async def _upsert_postgres_metrics(
        self,
        metric_date: date,
        dau: int,
        avg_watch_time: float,
        top_movies: list[dict[str, int | str]],
        conversion: dict[str, float | int],
        retention: list[dict[str, float | int | str]],
    ) -> None:
        metrics_payloads = [
            ("dau", json.dumps({"value": dau})),
            ("avg_watch_time", json.dumps({"value": avg_watch_time})),
            ("top_movies", json.dumps({"items": top_movies})),
            ("view_conversion", json.dumps(conversion)),
        ]

        await self._postgres.executemany(
            """
            INSERT INTO metrics (metric_date, metric_name, metric_value)
            VALUES ($1, $2, $3::jsonb)
            ON CONFLICT (metric_date, metric_name)
            DO UPDATE SET
                metric_value = EXCLUDED.metric_value,
                computed_at = NOW()
            """,
            [(metric_date, metric_name, payload) for metric_name, payload in metrics_payloads],
        )

        await self._postgres.execute(
            "DELETE FROM retention_cohorts WHERE cohort_date = $1",
            metric_date,
        )
        await self._postgres.executemany(
            """
            INSERT INTO retention_cohorts
            (cohort_date, day_of_life, cohort_size, returning_users, retention_pct)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (cohort_date, day_of_life)
            DO UPDATE SET
                cohort_size = EXCLUDED.cohort_size,
                returning_users = EXCLUDED.returning_users,
                retention_pct = EXCLUDED.retention_pct,
                computed_at = NOW()
            """,
            [
                (
                    metric_date,
                    int(row["day_of_life"]),
                    int(row["cohort_size"]),
                    int(row["returning_users"]),
                    float(row["retention_pct"]),
                )
                for row in retention
            ],
        )
