import asyncio
from datetime import date

import pytest

from api.missions import scheduler


def test_scheduler_runs_again_when_date_changes_during_generation(monkeypatch):
    dates = iter(
        [
            date(2026, 7, 27),
            date(2026, 7, 28),
            date(2026, 7, 28),
        ]
    )
    generation_count = 0

    async def fake_generate():
        nonlocal generation_count
        generation_count += 1
        if generation_count == 2:
            raise asyncio.CancelledError

    async def unexpected_sleep(_seconds):
        pytest.fail("The scheduler must not sleep after the date changes")

    monkeypatch.setattr(scheduler, "korea_today", lambda: next(dates))
    monkeypatch.setattr(scheduler, "_generate_missions_for_today", fake_generate)
    monkeypatch.setattr(scheduler.asyncio, "sleep", unexpected_sleep)

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(scheduler.run_daily_mission_scheduler())

    assert generation_count == 2
