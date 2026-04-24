from __future__ import annotations

from datetime import date

from clickhouse_client import ClickHouseClient


async def calculate_top_movies(
    clickhouse: ClickHouseClient,
    metric_date: date,
    limit: int,
) -> list[dict[str, int | str]]:
    rows = await clickhouse.fetch(
        """
        SELECT movie_id, count() AS view_count
        FROM events
        WHERE event_date = %(event_date)s
          AND event_type = 'VIEW_FINISHED'
        GROUP BY movie_id
        ORDER BY view_count DESC, movie_id ASC
        LIMIT %(limit)s
        """,
        {"event_date": metric_date, "limit": limit},
    )
    result: list[dict[str, int | str]] = []
    for index, row in enumerate(rows, start=1):
        result.append(
            {
                "movie_id": str(row[0]),
                "view_count": int(row[1]),
                "rank": index,
            }
        )
    return result
