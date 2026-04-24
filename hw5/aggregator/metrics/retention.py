from __future__ import annotations

from datetime import date

from clickhouse_client import ClickHouseClient


async def calculate_retention(clickhouse: ClickHouseClient, cohort_date: date) -> list[dict[str, float | int | str]]:
    cohort_size_rows = await clickhouse.fetch(
        """
        SELECT count()
        FROM
        (
            SELECT user_id
            FROM events
            WHERE event_type = 'VIEW_STARTED'
            GROUP BY user_id
            HAVING toDate(min(timestamp)) = %(cohort_date)s
        )
        """,
        {"cohort_date": cohort_date},
    )
    cohort_size = int(cohort_size_rows[0][0] if cohort_size_rows else 0)

    retention_rows = await clickhouse.fetch(
        """
        WITH first_views AS
        (
            SELECT user_id, toDate(min(timestamp)) AS cohort_date
            FROM events
            WHERE event_type = 'VIEW_STARTED'
            GROUP BY user_id
        )
        SELECT
            fv.cohort_date,
            dateDiff('day', fv.cohort_date, toDate(e.timestamp)) AS day_of_life,
            uniq(e.user_id) AS returning_users
        FROM events AS e
        INNER JOIN first_views AS fv ON e.user_id = fv.user_id
        WHERE fv.cohort_date = %(cohort_date)s
          AND dateDiff('day', fv.cohort_date, toDate(e.timestamp)) BETWEEN 0 AND 7
        GROUP BY fv.cohort_date, day_of_life
        ORDER BY day_of_life
        """,
        {"cohort_date": cohort_date},
    )

    by_day = {int(row[1]): int(row[2]) for row in retention_rows}
    result: list[dict[str, float | int | str]] = []
    for day_of_life in range(8):
        returning_users = by_day.get(day_of_life, 0)
        retention_pct = (returning_users / cohort_size * 100.0) if cohort_size else 0.0
        result.append(
            {
                "cohort_date": cohort_date.isoformat(),
                "day_of_life": day_of_life,
                "cohort_size": cohort_size,
                "returning_users": returning_users,
                "retention_pct": retention_pct,
            }
        )
    return result
