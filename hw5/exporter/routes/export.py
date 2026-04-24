from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query, Request

router = APIRouter()


@router.post("/export")
async def export_metrics(
    request: Request,
    metric_date: date = Query(..., alias="date"),
) -> dict[str, object]:
    runner = request.app.state.export_runner
    return await runner.run_for_date(metric_date)
