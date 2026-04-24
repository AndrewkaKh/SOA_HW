from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query, Request

router = APIRouter()


@router.post("/recalculate")
async def recalculate(
    request: Request,
    metric_date: date = Query(..., alias="date"),
) -> dict[str, object]:
    runner = request.app.state.aggregation_runner
    return await runner.run_for_date(metric_date)
