from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api.mission_service import get_daily_mission, get_latest_recovery_type
from api.routers.auth import get_current_user


router = APIRouter(prefix="/missions", tags=["missions"])


@router.get("/today")
def get_today_mission(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    recovery_type = get_latest_recovery_type(db, current_user.id)

    if recovery_type is None:
        raise HTTPException(status_code=404, detail="진단 결과가 없습니다.")

    mission = get_daily_mission(db, recovery_type, date.today())

    if mission is None:
        raise HTTPException(status_code=404, detail="오늘의 미션이 없습니다.")

    return mission
