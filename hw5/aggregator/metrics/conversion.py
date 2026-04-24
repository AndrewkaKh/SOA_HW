from __future__ import annotations

from datetime import date

from clickhouse_client import ClickHouseClient


async def calculate_conversion(clickhouse: ClickHouseClient, metric_date: date) -> dict[str, float | int]:
    rows = await clickhouse.fetch(
        """
        SELECT
            countIf(event_type = 'VIEW_STARTED') AS view_started_count,
            countIf(event_type = 'VIEW_FINISHED') AS view_finished_count
        FROM events
        WHERE event_date = %(event_date)s
        """,
        {"event_date": metric_date},
    )
    view_started_count = int(rows[0][0] if rows else 0)
    view_finished_count = int(rows[0][1] if rows else 0)
    conversion_ratio = (view_finished_count / view_started_count) if view_started_count else 0.0
    return {
        "view_started_count": view_started_count,
        "view_finished_count": view_finished_count,
        "conversion_ratio": float(conversion_ratio),
    }
