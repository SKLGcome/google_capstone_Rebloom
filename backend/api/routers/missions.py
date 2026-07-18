from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api.missions.service import get_daily_mission
from api.models import MissionCompletion
from api.recovery_types import normalize_recovery_type
from api.routers.auth import get_current_user


router = APIRouter(prefix="/missions", tags=["missions"])
KOREA_TIMEZONE = timezone(timedelta(hours=9))


def _recovery_type_from_room_id(room_id: str) -> str:
    """공용 회복 유형 채팅방 ID에서 회복 유형 코드를 추출한다."""

    prefix = "type_"
    if not room_id.startswith(prefix):
        raise HTTPException(
            status_code=400,
            detail="회복 유형 채팅방 ID는 type_REP 형식이어야 합니다.",
        )

    try:
        return normalize_recovery_type(room_id[len(prefix):])
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="지원하지 않는 회복 유형 채팅방입니다.",
        ) from exc


@router.get("/rooms/{room_id}/today")
def get_today_mission(
    room_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    recovery_type = _recovery_type_from_room_id(room_id)
    mission_date = datetime.now(KOREA_TIMEZONE).date()
    mission = get_daily_mission(db, recovery_type, mission_date)

    if mission is None:
        raise HTTPException(
            status_code=404,
            detail="이 채팅방의 오늘 미션이 없습니다.",
        )

    completion = (
        db.query(MissionCompletion)
        .filter(
            MissionCompletion.mission_id == mission.id,
            MissionCompletion.user_id == current_user.id,
        )
        .first()
    )

    return {
        "id": mission.id,
        "mission_name": mission.mission_name,
        "mission_date": mission.mission_date,
        "recovery_type": mission.recovery_type,
        "mission_content": mission.mission_content,
        "created_at": mission.created_at,
        "is_completed": completion is not None,
        "completed_at": completion.completed_at if completion else None,
    }


@router.post("/rooms/{room_id}/today/complete")
def complete_today_mission(
    room_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    recovery_type = _recovery_type_from_room_id(room_id)
    mission_date = datetime.now(KOREA_TIMEZONE).date()
    mission = get_daily_mission(db, recovery_type, mission_date)

    if mission is None:
        raise HTTPException(status_code=404, detail="이 채팅방의 오늘 미션이 없습니다.")

    completion = (
        db.query(MissionCompletion)
        .filter(
            MissionCompletion.mission_id == mission.id,
            MissionCompletion.user_id == current_user.id,
        )
        .first()
    )

    if completion is None:
        completion = MissionCompletion(mission_id=mission.id, user_id=current_user.id)
        db.add(completion)
        db.commit()
        db.refresh(completion)

    return {
        "mission_id": mission.id,
        "is_completed": True,
        "completed_at": completion.completed_at,
    }
