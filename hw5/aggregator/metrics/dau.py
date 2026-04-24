from __future__ import annotations

from datetime import date

from clickhouse_client import ClickHouseClient


async def calculate_dau(clickhouse: ClickHouseClient, metric_date: date) -> int:
    rows = await clickhouse.fetch(
        """
        SELECT uniq(user_id)
        FROM events
        WHERE event_date = %(event_date)s
        """,
        {"event_date": metric_date},
    )
    return int(rows[0][0] if rows else 0)
