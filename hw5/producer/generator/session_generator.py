from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from faker import Faker

from models import DeviceType, EventType, MovieEvent

faker = Faker()


class SessionGenerator:
    def __init__(self, backfill_days: int) -> None:
        self._backfill_days = backfill_days
        self._movie_ids = [f"movie-{index:03d}" for index in range(1, 31)]
        self._stable_users = [f"user-{index:03d}" for index in range(1, 81)]

    def generate_backfill_events(self) -> list[MovieEvent]:
        events: list[MovieEvent] = []
        today = datetime.now(timezone.utc).date()
        for day_offset in range(self._backfill_days, 0, -1):
            day = today - timedelta(days=day_offset)
            for _ in range(18):
                user_id = random.choice(self._stable_users)
                session_start = datetime.combine(
                    day,
                    datetime.min.time(),
                    tzinfo=timezone.utc,
                ) + timedelta(minutes=random.randint(0, 1439))
                events.extend(self._generate_session(user_id=user_id, started_at=session_start))
        return events

    def generate_live_events(self) -> list[MovieEvent]:
        active_user = random.choice(self._stable_users)
        started_at = datetime.now(timezone.utc)
        return self._generate_session(user_id=active_user, started_at=started_at)

    def _generate_session(self, user_id: str, started_at: datetime) -> list[MovieEvent]:
        session_id = str(uuid4())
        movie_id = random.choice(self._movie_ids)
        device_type = random.choice(list(DeviceType))
        progress_points = sorted(random.sample(range(45, 7200), 2))
        finish_progress = progress_points[-1] + random.randint(60, 900)

        events = [
            MovieEvent(
                user_id=user_id,
                movie_id=movie_id,
                event_type=EventType.SEARCHED,
                timestamp=started_at - timedelta(seconds=random.randint(5, 30)),
                device_type=device_type,
                session_id=session_id,
                progress_seconds=0,
            ),
            MovieEvent(
                user_id=user_id,
                movie_id=movie_id,
                event_type=EventType.VIEW_STARTED,
                timestamp=started_at,
                device_type=device_type,
                session_id=session_id,
                progress_seconds=0,
            ),
            MovieEvent(
                user_id=user_id,
                movie_id=movie_id,
                event_type=EventType.VIEW_PAUSED,
                timestamp=started_at + timedelta(seconds=progress_points[0]),
                device_type=device_type,
                session_id=session_id,
                progress_seconds=progress_points[0],
            ),
            MovieEvent(
                user_id=user_id,
                movie_id=movie_id,
                event_type=EventType.VIEW_RESUMED,
                timestamp=started_at + timedelta(seconds=progress_points[0] + random.randint(10, 120)),
                device_type=device_type,
                session_id=session_id,
                progress_seconds=progress_points[0],
            ),
            MovieEvent(
                user_id=user_id,
                movie_id=movie_id,
                event_type=EventType.VIEW_FINISHED,
                timestamp=started_at + timedelta(seconds=finish_progress),
                device_type=device_type,
                session_id=session_id,
                progress_seconds=finish_progress,
            ),
        ]

        if random.random() < 0.45:
            events.append(
                MovieEvent(
                    user_id=user_id,
                    movie_id=movie_id,
                    event_type=EventType.LIKED,
                    timestamp=events[-1].timestamp + timedelta(seconds=random.randint(5, 90)),
                    device_type=device_type,
                    session_id=session_id,
                    progress_seconds=0,
                )
            )

        return sorted(events, key=lambda item: item.timestamp)
