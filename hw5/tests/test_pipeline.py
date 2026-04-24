from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import httpx


def test_event_reaches_clickhouse(producer_base_url, clickhouse_client) -> None:
    event_id = str(uuid4())
    user_id = f"user-{uuid4()}"
    session_id = str(uuid4())
    payload = {
        "event_id": event_id,
        "user_id": user_id,
        "movie_id": "movie-test-001",
        "event_type": "VIEW_FINISHED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "device_type": "DESKTOP",
        "session_id": session_id,
        "progress_seconds": 321,
    }

    response = httpx.post(f"{producer_base_url}/events", json=payload, timeout=10.0)
    response.raise_for_status()
    assert response.json()["event_id"] == event_id

    for _ in range(30):
        rows = clickhouse_client.execute(
            """
            SELECT event_id, user_id, movie_id, event_type, device_type, session_id, progress_seconds
            FROM events FINAL
            WHERE event_id = %(event_id)s
            """,
            {"event_id": event_id},
        )
        if rows:
            break
        import time

        time.sleep(1)
    else:
        raise AssertionError("Event did not appear in ClickHouse within 30 seconds")

    event_row = rows[0]
    assert event_row[0] == event_id
    assert event_row[1] == user_id
    assert event_row[2] == "movie-test-001"
    assert event_row[3] == "VIEW_FINISHED"
    assert event_row[4] == "DESKTOP"
    assert event_row[5] == session_id
    assert event_row[6] == 321
