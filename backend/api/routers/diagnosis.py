import traceback

from fastapi import APIRouter, Depends, HTTPException

from api.agent import run_diagnosis_agent
from api.models import User
from api.neo4j import graph
from api.routers.auth import get_current_user

router = APIRouter()


@router.get("/diagnosis/latest")
async def get_latest_diagnosis(current_user: User = Depends(get_current_user)):
    try:
        result = graph.query(
            """
            MATCH (u:User {nickname: $nickname})
            OPTIONAL MATCH (u)-[:HAS_STRENGTH]->(strength:Topic)
            OPTIONAL MATCH (u)-[:NEEDS]->(need:Topic)
            OPTIONAL MATCH (u)-[:HAS_GOAL]->(goal:Goal)
            RETURN
                u.recovery_type AS type,
                u.summary AS summary,
                collect(DISTINCT strength.name) AS strengthTopics,
                collect(DISTINCT need.name) AS needTopics,
                head(collect(DISTINCT goal.name)) AS goal,
                {
                    energy: u.energy,
                    direction: u.direction,
                    action: u.action
                } AS scores
            """,
            params={"nickname": current_user.nickname},
        )

        if not result or not result[0].get("type"):
            raise HTTPException(status_code=404, detail="저장된 진단 결과가 없습니다.")

        return result[0]
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="최신 진단 조회 실패") from e


@router.post("/diagnosis")
async def diagnosis(
    request: dict,
    current_user: User = Depends(get_current_user),
):
    try:
        messages = request.get("messages", [])
        conversation = "\n".join(
            [f"{message['role']}: {message['content']}" for message in messages]
        )

        return run_diagnosis_agent(
            nickname=current_user.nickname,
            conversation=conversation,
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="진단 처리 실패") from e
