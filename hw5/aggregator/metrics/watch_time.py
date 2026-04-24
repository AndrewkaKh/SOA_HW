from __future__ import annotations

from datetime import date

from clickhouse_client import ClickHouseClient


async def calculate_watch_time(clickhouse: ClickHouseClient, metric_date: date) -> float:
    rows = await clickhouse.fetch(
        """
        SELECT avg(progress_seconds)
        FROM events
        WHERE event_date = %(event_date)s
          AND event_type = 'VIEW_FINISHED'
        """,
        {"event_date": metric_date},
    )
    value = rows[0][0] if rows and rows[0][0] is not None else 0.0
    return float(value)
