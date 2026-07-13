from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from api.database import SessionLocal
from api.models import ChatMessage, DailyMission, Diagnosis
from api.schemas import RoomMessage


RECOVERY_TYPES = (
    "REP",
    "RED",
    "RCP",
    "RCD",
    "AEP",
    "AED",
    "ACP",
    "ACD",
)


def load_room_context(
    room_id: str,
    hours: int = 48,
    limit: int = 100,
) -> list[dict]:
    """Return recent messages from one chat room."""

    safe_hours = min(max(hours, 1), 168)
    safe_limit = min(max(limit, 1), 200)
    since = datetime.utcnow() - timedelta(hours=safe_hours)

    with SessionLocal() as db:
        messages = (
            db.query(ChatMessage)
            .filter(
                ChatMessage.room_id == room_id,
                ChatMessage.created_at >= since,
                ChatMessage.content.isnot(None),
                ChatMessage.content != "",
            )
            .order_by(ChatMessage.created_at.desc())
            .limit(safe_limit)
            .all()
        )

    return [
        RoomMessage(content=message.content).model_dump()
        for message in reversed(messages)
    ]


def load_all_type_contexts(
    hours: int = 48,
    limit_per_type: int = 100,
) -> dict[str, list[dict]]:
    """Return recent messages grouped by every recovery type."""

    return {
        recovery_type: load_room_context(
            room_id=f"type_{recovery_type}",
            hours=hours,
            limit=limit_per_type,
        )
        for recovery_type in RECOVERY_TYPES
    }


def get_latest_recovery_type(db: Session, user_id: int) -> str | None:
    diagnosis = (
        db.query(Diagnosis)
        .filter(Diagnosis.user_id == user_id)
        .order_by(Diagnosis.created_at.desc())
        .first()
    )
    return diagnosis.recovery_type if diagnosis else None


def get_daily_mission(
    db: Session,
    recovery_type: str,
    mission_date: date,
) -> DailyMission | None:
    return (
        db.query(DailyMission)
        .filter(
            DailyMission.recovery_type == recovery_type,
            DailyMission.mission_date == mission_date,
        )
        .first()
    )
