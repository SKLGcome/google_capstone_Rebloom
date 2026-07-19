"""검색 문서가 미션 생성 근거로 충분한지 LLM으로 평가한다."""

import os
from typing import Any

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from api.rag.document_loader import BACKEND_DIR
from api.rag.schemas import RetrievalEvaluation
from api.recovery_types import describe_recovery_type


load_dotenv(BACKEND_DIR / ".env")

DEFAULT_EVALUATION_MODEL = "gemini-2.5-flash"
DEFAULT_MAX_CONTEXT_CHARS = 12_000


def _get_evaluation_model() -> BaseChatModel:
    """검색 결과 평가에 사용할 모델을 생성한다."""

    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY가 없어 검색 결과를 평가할 수 없습니다.")

    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_CHAT_MODEL", DEFAULT_EVALUATION_MODEL),
        temperature=0,
    )


def _format_documents(
    documents: list[Document],
    *,
    max_context_chars: int = DEFAULT_MAX_CONTEXT_CHARS,
) -> str:
    """Retriever의 Document 목록을 출처가 보존된 평가 컨텍스트로 바꾼다."""

    if max_context_chars < 1:
        raise ValueError("max_context_chars must be at least 1")

    sections: list[str] = []
    used_chars = 0

    for index, document in enumerate(documents, start=1):
        content = document.page_content.strip()
        if not content:
            continue

        metadata = document.metadata
        source = metadata.get("file_name") or metadata.get("source") or "unknown"
        page = metadata.get("page", "unknown")
        chunk_index = metadata.get("chunk_index", "unknown")
        header = (
            f"[문서 {index}] 출처={source}, 페이지={page}, 청크={chunk_index}\n"
        )
        remaining = max_context_chars - used_chars - len(header)
        if remaining <= 0:
            break

        section = header + content[:remaining]
        sections.append(section)
        used_chars += len(section)

        if used_chars >= max_context_chars:
            break

    return "\n\n".join(sections)


def evaluate_retrieval(
    recovery_type: str,
    community_summary: str,
    query: str,
    documents: list[Document],
    *,
    llm: BaseChatModel | Any | None = None,
    max_context_chars: int = DEFAULT_MAX_CONTEXT_CHARS,
) -> RetrievalEvaluation:
    """검색 결과를 평가하고, 부족하면 다음 검색 query를 제안한다.

    이 함수는 검색을 직접 실행하지 않는다. 호출 측 워크플로가 반환된
    ``revised_query``를 이용해 재검색 여부와 최대 시도 횟수를 통제한다.
    """

    normalized_type = recovery_type.strip().upper()
    normalized_summary = community_summary.strip()
    normalized_query = query.strip()

    if not normalized_type:
        raise ValueError("recovery_type must not be empty")
    if not normalized_query:
        raise ValueError("query must not be empty")

    type_description = describe_recovery_type(normalized_type)
    community_context = normalized_summary or "최근 커뮤니티 대화 맥락 없음"

    document_context = _format_documents(
        documents,
        max_context_chars=max_context_chars,
    )
    if not document_context:
        return RetrievalEvaluation(
            sufficient=False,
            relevance_score=0,
            reason="검색된 문서가 없어 미션 생성 근거를 확인할 수 없습니다.",
            missing_information=["실행 가능한 미션 행동과 난이도에 관한 근거"],
            revised_query=(
                f"{normalized_type} {type_description} {normalized_summary} "
                "부담이 적고 구체적인 일상 실천 활동"
            ).strip(),
        )

    prompt = f"""
[회복 유형]
{normalized_type}

[회복 유형 설명]
{type_description}

[커뮤니티 요약]
{community_context}

[현재 검색 query]
{normalized_query}

[검색 문서]
{document_context}

위 검색 문서만으로 커뮤니티 상태에 맞는 오늘의 미션을 만들 수 있는지 평가하세요.

평가 기준:
1. 회복 유형과 커뮤니티의 감정·상태에 관련되어 있는가
2. 사용자가 실제로 수행할 구체적인 행동의 근거가 있는가
3. 행동의 난이도와 수행 방법을 정할 근거가 있는가
4. 문서에 없는 의학적·심리학적 효과를 추측하지 않고 미션을 만들 수 있는가

충분하면 sufficient=true, revised_query=null로 답하세요.
부족하면 sufficient=false로 답하고, 부족한 정보를 missing_information에 적은 뒤
이를 보완할 짧고 구체적인 한국어 검색어를 revised_query로 작성하세요.
relevance_score는 0부터 100 사이의 정수로 작성하세요.
""".strip()

    evaluation_model = llm or _get_evaluation_model()
    structured_model = evaluation_model.with_structured_output(RetrievalEvaluation)
    result = structured_model.invoke(
        [
            SystemMessage(
                content=(
                    "당신은 미션 생성용 RAG 검색 결과의 관련성과 충분성을 "
                    "엄격하게 검증하는 평가 에이전트입니다."
                )
            ),
            HumanMessage(content=prompt),
        ]
    )

    evaluation = (
        result
        if isinstance(result, RetrievalEvaluation)
        else RetrievalEvaluation.model_validate(result)
    )

    # LLM 출력 보정은 데이터 모델이 아니라 평가 단계의 정책으로 처리한다.
    if evaluation.sufficient:
        evaluation.missing_information = []
        evaluation.revised_query = None
    elif evaluation.revised_query is not None:
        evaluation.revised_query = evaluation.revised_query.strip() or None

    return evaluation
