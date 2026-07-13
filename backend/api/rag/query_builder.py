"""회복 유형별 커뮤니티 대화를 요약해 검색 질의를 생성한다."""

import os
from collections.abc import Iterable, Mapping
from typing import Any

from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from api.rag.document_loader import BACKEND_DIR


load_dotenv(BACKEND_DIR / ".env")

DEFAULT_SUMMARY_MODEL = "gemini-2.5-flash"


def _get_summary_model() -> BaseChatModel:
    """커뮤니티 대화 요약에 사용할 LLM을 생성한다."""

    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY가 있어야 검색 질의를 생성할 수 있습니다.")

    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_CHAT_MODEL", DEFAULT_SUMMARY_MODEL),
        temperature=0,
    )


def _summarize_messages(
    recovery_type: str,
    community_messages: Iterable[Mapping[str, Any]],
    *,
    llm: BaseChatModel | Any | None = None,
) -> str:
    """커뮤니티 대화 전체를 미션 검색에 적합한 내용으로 요약한다."""

    conversation = "\n".join(
        text
        for message in community_messages
        if (text := str(message.get("content") or "").strip())
    )

    if not conversation:
        return "최근 커뮤니티 대화가 없습니다."

    prompt = f"""
다음은 {recovery_type} 회복 유형 커뮤니티에서 나눈 대화입니다.

대화:
{conversation}

이 대화를 일일 미션 검색에 사용할 수 있도록 2~3문장으로 요약하세요.
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
            SystemMessage(content="커뮤니티 대화를 미션 검색용으로 요약하는 AI입니다."),
            HumanMessage(content=prompt),
        ]
    )
    summary = str(response.content).strip()

    if not summary:
        raise RuntimeError("LLM이 커뮤니티 대화 요약을 반환하지 않았습니다.")

    return summary


def build_retrieval_query(
    recovery_type: str,
    community_messages: Iterable[Mapping[str, Any]],
    *,
    llm: BaseChatModel | Any | None = None,
) -> str:
    """커뮤니티 대화를 요약하고 회복 유형과 결합해 검색 질의를 생성한다."""

    normalized_type = recovery_type.strip().upper()
    if not normalized_type:
        raise ValueError("recovery_type must not be empty")

    summary = _summarize_messages(
        recovery_type=normalized_type,
        community_messages=community_messages,
        llm=llm,
    )

    return (
        f"회복 유형: {normalized_type}\n"
        f"커뮤니티 대화 요약: {summary}"
    )
