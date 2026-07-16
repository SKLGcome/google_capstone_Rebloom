"""한국 시간 자정마다 모든 회복 유형의 미션을 생성한다."""

import asyncio
import logging
from datetime import date, datetime, time, timedelta, timezone

from api.mission_workflow import generate_all_daily_missions


logger = logging.getLogger(__name__)
KOREA_TIMEZONE = timezone(timedelta(hours=9))


def korea_today() -> date:
    """현재 한국 날짜를 반환한다."""

    return datetime.now(KOREA_TIMEZONE).date()


def seconds_until_next_midnight(now: datetime | None = None) -> float:
    """다음 한국 시간 자정까지 남은 초를 계산한다."""

    current = now or datetime.now(KOREA_TIMEZONE)
    if current.tzinfo is None:
        current = current.replace(tzinfo=KOREA_TIMEZONE)
    else:
        current = current.astimezone(KOREA_TIMEZONE)

    tomorrow = current.date() + timedelta(days=1)
    next_midnight = datetime.combine(
        tomorrow,
        time.min,
        tzinfo=KOREA_TIMEZONE,
    )
    return max((next_midnight - current).total_seconds(), 0.0)


async def _generate_missions_for_today() -> None:
    """동기 LLM·DB 작업을 별도 스레드에서 실행한다."""

    mission_date = korea_today()
    results = await asyncio.to_thread(
        generate_all_daily_missions,
        mission_date,
    )
    failed_types = [
        recovery_type
        for recovery_type, result in results.items()
        if not result["success"]
    ]

    if failed_types:
        logger.error(
            "Daily mission generation failed for %s: %s",
            mission_date,
            failed_types,
        )
        for recovery_type in failed_types:
            logger.error(
                "Mission generation error for recovery_type=%s date=%s: %s",
                recovery_type,
                mission_date,
                results[recovery_type].get("error", "Unknown error"),
            )
    else:
        logger.info("Daily missions generated for %s", mission_date)


async def run_daily_mission_scheduler() -> None:
    """서버 시작 시 누락 미션을 채우고 이후 매일 자정에 실행한다."""

    while True:
        try:
            await _generate_missions_for_today()
        except asyncio.CancelledError:
            logger.info("Daily mission scheduler stopped")
            raise
        except Exception:
            logger.exception("Daily mission generation failed unexpectedly")

        await asyncio.sleep(seconds_until_next_midnight())
