from datetime import date

from sqlalchemy.orm import Session

from api.database import SessionLocal
from api.mission_service import (
    generate_mission,
    get_daily_mission,
    load_room_context,
    save_daily_mission,
    summarize_community_messages,
)
from api.models import DailyMission
from api.rag.evaluator import evaluate_retrieval
from api.rag.query_builder import build_retrieval_query
from api.rag.retriever import retrieve_mission_documents
from api.recovery_types import RECOVERY_TYPES


MAX_RETRIEVAL_ATTEMPTS = 3


def run_mission_workflow(
    db: Session,
    recovery_type: str,
    mission_date: date,
) -> DailyMission:
    normalized_type = recovery_type.strip().upper()

    if not normalized_type:
        raise ValueError("recovery_type must not be empty")

    # 1. 이미 오늘 미션이 있으면 생성하지 않음
    existing_mission = get_daily_mission(
        db=db,
        recovery_type=normalized_type,
        mission_date=mission_date,
    )

    if existing_mission is not None:
        return existing_mission

    # 2. 해당 회복 유형의 커뮤니티 메시지 조회
    community_messages = load_room_context(
        room_id=f"type_{normalized_type}",
    )

    # 3. 커뮤니티 메시지 요약
    community_summary = summarize_community_messages(
        recovery_type=normalized_type,
        community_messages=community_messages,
    )

    # 4. LLM이 초기 검색 query 생성
    retrieval_query = build_retrieval_query(
        recovery_type=normalized_type,
        community_summary=community_summary,
    )

    query = retrieval_query.query
    documents = []
    best_documents = []
    best_relevance_score = -1

    # 5. 검색 → 평가 → 필요하면 query 수정
    for attempt in range(MAX_RETRIEVAL_ATTEMPTS):
        documents = retrieve_mission_documents(query)

        evaluation = evaluate_retrieval(
            recovery_type=normalized_type,
            community_summary=retrieval_query.community_summary,
            query=query,
            documents=documents,
        )

        if documents and evaluation.relevance_score > best_relevance_score:
            best_documents = documents
            best_relevance_score = evaluation.relevance_score

        if evaluation.sufficient:
            best_documents = documents
            break

        if not evaluation.revised_query:
            break

        query = evaluation.revised_query

    documents = best_documents

    # 6. 검색이 충분하지 않아도 현재 문서와 커뮤니티 맥락으로 미션 생성
    generated_mission = generate_mission(
        recovery_type=normalized_type,
        community_summary=retrieval_query.community_summary,
        documents=documents,
    )

    # 7. DB 저장
    return save_daily_mission(
        db=db,
        mission=generated_mission,
        mission_date=mission_date,
    )


def generate_all_daily_missions(mission_date: date) -> dict[str, dict]:
    """모든 회복 유형의 일일 미션을 생성하고 유형별 결과를 반환한다."""

    results: dict[str, dict] = {}

    with SessionLocal() as db:
        for recovery_type in RECOVERY_TYPES:
            try:
                mission = run_mission_workflow(
                    db=db,
                    recovery_type=recovery_type,
                    mission_date=mission_date,
                )
                results[recovery_type] = {
                    "success": True,
                    "mission_id": mission.id,
                    "mission_name": mission.mission_name,
                }
            except Exception as exc:
                db.rollback()
                results[recovery_type] = {
                    "success": False,
                    "error": str(exc),
                }

    return results
