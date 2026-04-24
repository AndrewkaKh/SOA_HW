from __future__ import annotations

import asyncio

from fastapi import APIRouter, Request

from models import EventAccepted, MovieEvent

router = APIRouter()


@router.post("/events", response_model=EventAccepted)
async def create_event(request: Request, event: MovieEvent) -> EventAccepted:
    producer = request.app.state.event_producer
    await asyncio.to_thread(producer.send_with_retry, event.to_kafka_dict(), event.user_id)
    return EventAccepted(event_id=event.event_id)
