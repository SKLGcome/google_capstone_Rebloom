"""회복 유형과 커뮤니티 요약을 바탕으로 검색 query를 생성한다."""

import os
from typing import Any

from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from api.rag.document_loader import BACKEND_DIR
from api.rag.schemas import RetrievalQuery
from api.recovery_types import describe_recovery_type


load_dotenv(BACKEND_DIR / ".env")

DEFAULT_QUERY_MODEL = "gemini-2.5-flash"


def _get_query_model() -> BaseChatModel:
    """미션 문서 검색 query 생성에 사용할 LLM을 생성한다."""

    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY가 있어야 검색 질의를 생성할 수 있습니다.")

    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_CHAT_MODEL", DEFAULT_QUERY_MODEL),
        temperature=0,
    )


def build_retrieval_query(
    recovery_type: str,
    community_summary: str = "",
    *,
    llm: BaseChatModel | Any | None = None,
) -> RetrievalQuery:
    """LLM이 검색 query를 만들고 평가에 필요한 요약과 함께 반환한다."""

    normalized_type = recovery_type.strip().upper()
    normalized_summary = community_summary.strip()
    if not normalized_type:
        raise ValueError("recovery_type must not be empty")

    type_description = describe_recovery_type(normalized_type)
    community_context = normalized_summary or "최근 커뮤니티 대화 맥락 없음"

    prompt = f"""
다음 커뮤니티 상황에 적합한 일일 미션의 근거 문서를 검색하려고 합니다.

회복 유형 코드:
{normalized_type}

회복 유형 설명:
{type_description}

커뮤니티 요약:
{community_context}

다음 내용을 찾을 수 있도록 검색 query를 한 줄로 작성하세요.
- 회복 유형의 에너지·방향성·행동 상태에 적합한 행동
- 커뮤니티 맥락이 있으면 현재 공통 감정과 선호 활동
- 부담 없이 수행할 수 있는 활동 강도
- 구체적인 수행 방법과 시간
- 피해야 할 행동이나 강도

핵심 키워드와 검색 의도가 드러나는 한국어 검색 query만 반환하세요.
설명이나 따옴표는 포함하지 마세요.
""".strip()

    query_model = llm or _get_query_model()
    response = query_model.invoke(
        [
            SystemMessage(content="미션 문서 검색 query를 설계하는 AI입니다."),
            HumanMessage(content=prompt),
        ]
    )
    query = str(response.content).strip()
    if not query:
        raise RuntimeError("LLM이 검색 query를 반환하지 않았습니다.")

    return RetrievalQuery(
        community_summary=normalized_summary,
        query=query,
    )
