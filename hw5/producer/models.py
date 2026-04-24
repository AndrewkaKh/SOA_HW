from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


class EventType(str, Enum):
    VIEW_STARTED = "VIEW_STARTED"
    VIEW_FINISHED = "VIEW_FINISHED"
    VIEW_PAUSED = "VIEW_PAUSED"
    VIEW_RESUMED = "VIEW_RESUMED"
    LIKED = "LIKED"
    SEARCHED = "SEARCHED"


class DeviceType(str, Enum):
    MOBILE = "MOBILE"
    DESKTOP = "DESKTOP"
    TV = "TV"
    TABLET = "TABLET"


NON_PROGRESS_EVENT_TYPES = {EventType.LIKED, EventType.SEARCHED}


class MovieEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    user_id: str
    movie_id: str
    event_type: EventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    device_type: DeviceType
    session_id: str
    progress_seconds: int = 0

    @field_validator("timestamp", mode="before")
    @classmethod
    def ensure_timezone(cls, value: datetime) -> datetime:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        return value

    @field_validator("progress_seconds")
    @classmethod
    def ensure_non_negative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("progress_seconds must be non-negative")
        return value

    @model_validator(mode="after")
    def validate_progress_rule(self) -> "MovieEvent":
        if self.event_type in NON_PROGRESS_EVENT_TYPES and self.progress_seconds != 0:
            raise ValueError("LIKED and SEARCHED events must have progress_seconds = 0")
        return self

    def to_kafka_dict(self) -> dict[str, object]:
        return {
            "event_id": str(self.event_id),
            "user_id": self.user_id,
            "movie_id": self.movie_id,
            "event_type": self.event_type.value,
            "timestamp": int(self.timestamp.timestamp() * 1_000_000),
            "device_type": self.device_type.value,
            "session_id": self.session_id,
            "progress_seconds": self.progress_seconds,
        }


class EventAccepted(BaseModel):
    event_id: UUID


class HealthResponse(BaseModel):
    status: str = "ok"
