import os
from collections.abc import Iterable, Mapping
from datetime import date, datetime, timedelta
from typing import Any

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from sqlalchemy.orm import Session

from api.database import SessionLocal
from api.models import ChatMessage, DailyMission, Diagnosis
from api.rag.document_loader import BACKEND_DIR
from api.rag.schemas import GeneratedMission
from api.recovery_types import RECOVERY_TYPES, describe_recovery_type
from api.schemas import RoomMessage


load_dotenv(BACKEND_DIR / ".env")

DEFAULT_SUMMARY_MODEL = "gemini-2.5-flash"
DEFAULT_MISSION_MODEL = "gemini-2.5-flash"
DEFAULT_MAX_MISSION_CONTEXT_CHARS = 12_000

def _get_summary_model() -> BaseChatModel:
    """커뮤니티 대화 요약에 사용할 LLM을 생성한다."""

    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY가 있어야 커뮤니티 대화를 요약할 수 있습니다.")

    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_CHAT_MODEL", DEFAULT_SUMMARY_MODEL),
        temperature=0,
    )


def summarize_community_messages(
    recovery_type: str,
    community_messages: Iterable[Mapping[str, Any]],
    *,
    llm: BaseChatModel | Any | None = None,
) -> str:
    """회복 유형별 커뮤니티 대화를 미션 생성용 컨텍스트로 요약한다."""

    normalized_type = recovery_type.strip().upper()
    if not normalized_type:
        raise ValueError("recovery_type must not be empty")

    conversation = "\n".join(
        text
        for message in community_messages
        if (text := str(message.get("content") or "").strip())
    )
    if not conversation:
        return ""

    prompt = f"""
다음은 {normalized_type} 회복 유형 커뮤니티에서 나눈 대화입니다.

대화:
{conversation}

이 대화를 일일 미션 생성에 사용할 수 있도록 2~3문장으로 요약하세요.
다음 내용을 중심으로 작성하세요.
- 사용자들의 공통 감정과 상태
- 선호하는 활동
- 피하고 싶은 활동
- 부담 없이 실천할 수 있는 활동 강도

추측하거나 개인을 식별할 수 있는 정보는 포함하지 말고 요약문만 반환하세요.
""".strip()

    summary_model = llm or _get_summary_model()
    response = summary_model.invoke(
        [
            SystemMessage(content="커뮤니티 대화를 일일 미션 생성용으로 요약하는 AI입니다."),
            HumanMessage(content=prompt),
        ]
    )
    summary = str(response.content).strip()
    if not summary:
        raise RuntimeError("LLM이 커뮤니티 대화 요약을 반환하지 않았습니다.")

    return summary


def _get_mission_model() -> BaseChatModel:
    """검색 문서 기반 미션 생성에 사용할 LLM을 생성한다."""

    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY가 있어야 미션을 생성할 수 있습니다.")

    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_CHAT_MODEL", DEFAULT_MISSION_MODEL),
        temperature=0,
    )


def _format_mission_documents(
    documents: list[Document],
    *,
    max_context_chars: int = DEFAULT_MAX_MISSION_CONTEXT_CHARS,
) -> tuple[str, set[str]]:
    """검색 문서를 생성 프롬프트로 바꾸고 사용 가능한 근거 ID를 반환한다."""

    if max_context_chars < 1:
        raise ValueError("max_context_chars must be at least 1")

    sections: list[str] = []
    evidence_ids: set[str] = set()
    used_chars = 0

    for index, document in enumerate(documents, start=1):
        content = document.page_content.strip()
        if not content:
            continue

        evidence_id = f"document-{index}"
        metadata = document.metadata
        source = metadata.get("file_name") or metadata.get("source") or "unknown"
        page = metadata.get("page", "unknown")
        chunk_index = metadata.get("chunk_index", "unknown")
        header = (
            f"[{evidence_id}] 출처={source}, 페이지={page}, 청크={chunk_index}\n"
        )
        remaining = max_context_chars - used_chars - len(header)
        if remaining <= 0:
            break

        section = header + content[:remaining]
        sections.append(section)
        evidence_ids.add(evidence_id)
        used_chars += len(section)

        if used_chars >= max_context_chars:
            break

    return "\n\n".join(sections), evidence_ids


def generate_mission(
    recovery_type: str,
    community_summary: str,
    documents: list[Document],
    *,
    llm: BaseChatModel | Any | None = None,
    max_context_chars: int = DEFAULT_MAX_MISSION_CONTEXT_CHARS,
) -> GeneratedMission:
    """검색 문서를 우선 참고하고, 없으면 유형과 대화 맥락으로 미션을 생성한다."""

    normalized_type = recovery_type.strip().upper()
    normalized_summary = community_summary.strip()
    if not normalized_type:
        raise ValueError("recovery_type must not be empty")

    type_description = describe_recovery_type(normalized_type)
    community_context = (
        normalized_summary
        if normalized_summary
        else "최근 커뮤니티 대화 맥락 없음"
    )

    document_context, allowed_evidence = _format_mission_documents(
        documents,
        max_context_chars=max_context_chars,
    )

    if document_context:
        evidence_context = f"""
[참고할 검색 문서]
{document_context}

문서에서 실제 사용한 근거 ID를 evidence에 한 개 이상 작성하세요.
문서에 없는 효과나 사실은 추가하지 마세요.
""".strip()
    else:
        evidence_context = """
[참고할 검색 문서]
충분한 검색 문서를 찾지 못했습니다.

회복 유형 설명과 커뮤니티 요약만 사용해 부담이 적은 미션을 만드세요.
의학적·심리학적 효과를 주장하지 말고 evidence는 빈 목록으로 작성하세요.
""".strip()

    prompt = f"""
[회복 유형]
{normalized_type}

[회복 유형 설명]
{type_description}

[커뮤니티 요약]
{community_context}

{evidence_context}

오늘 수행할 일일 미션 하나를 생성하세요.

사용 가능한 정보는 다음 우선순위로 반영하세요.
1. 유형 설명, 커뮤니티 맥락, 검색 문서가 모두 있으면 세 정보를 함께 반영합니다.
2. 커뮤니티 맥락이나 검색 문서 중 하나만 있으면 유형 설명과 해당 정보를 반영합니다.
3. 둘 다 없으면 유형 설명만으로 안전하고 부담이 적은 미션을 만듭니다.

생성 규칙:
1. 한 번에 하나의 구체적인 행동만 제안하세요.
2. 특별한 장비 없이 일상에서 부담 없이 수행할 수 있어야 합니다.
3. 수행 시간이나 완료 기준을 명확하게 작성하세요.
4. 의학적 진단이나 문서에 없는 효과를 만들어내지 마세요.
5. 명령하거나 실패를 탓하는 표현을 사용하지 마세요.
6. recovery_type은 반드시 {normalized_type}으로 작성하세요.
""".strip()

    mission_model = llm or _get_mission_model()
    structured_model = mission_model.with_structured_output(GeneratedMission)
    result = structured_model.invoke(
        [
            SystemMessage(
                content="검색 문서에 근거해 부담이 적은 일일 미션을 만드는 AI입니다."
            ),
            HumanMessage(content=prompt),
        ]
    )
    mission = (
        result
        if isinstance(result, GeneratedMission)
        else GeneratedMission.model_validate(result)
    )

    mission.recovery_type = mission.recovery_type.strip().upper()
    if mission.recovery_type != normalized_type:
        raise RuntimeError("LLM이 요청과 다른 recovery_type을 반환했습니다.")

    mission.evidence = list(
        dict.fromkeys(item.strip() for item in mission.evidence if item.strip())
    )
    if not allowed_evidence:
        mission.evidence = []
        return mission

    invalid_evidence = set(mission.evidence) - allowed_evidence
    if invalid_evidence:
        raise RuntimeError(
            f"LLM이 검색 문서에 없는 근거 ID를 반환했습니다: {sorted(invalid_evidence)}"
        )
    if not mission.evidence:
        raise RuntimeError("LLM이 미션 근거를 반환하지 않았습니다.")

    return mission


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


def save_daily_mission(
    db: Session,
    mission: GeneratedMission,
    mission_date: date,
) -> DailyMission:
    """같은 회복 유형과 날짜의 미션이 없을 때 생성 결과를 저장한다."""

    normalized_type = mission.recovery_type.strip().upper()
    existing = get_daily_mission(db, normalized_type, mission_date)
    if existing is not None:
        return existing

    daily_mission = DailyMission(
        mission_name=mission.mission_name.strip(),
        mission_content=mission.mission_content.strip(),
        recovery_type=normalized_type,
        mission_date=mission_date,
    )
    db.add(daily_mission)
    db.commit()
    db.refresh(daily_mission)
    return daily_mission
