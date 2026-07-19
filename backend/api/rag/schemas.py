"""Agentic RAG에서 사용하는 구조화 데이터 모델."""

from pydantic import BaseModel, Field


class RetrievalQuery(BaseModel):
    """검색과 평가 단계에 함께 전달할 커뮤니티 요약 및 검색 query."""

    community_summary: str = ""
    query: str = Field(min_length=1)


class RetrievalEvaluation(BaseModel):
    """검색 문서가 미션 생성에 충분한지에 대한 LLM 평가 결과."""

    sufficient: bool
    relevance_score: int = Field(ge=0, le=100)
    reason: str = Field(min_length=1)
    missing_information: list[str] = Field(default_factory=list)
    revised_query: str | None = None


class GeneratedMission(BaseModel):
    """검색 문서를 근거로 생성한 일일 미션."""

    mission_name: str = Field(min_length=1, max_length=100)
    mission_content: str = Field(min_length=1)
    recovery_type: str = Field(min_length=1)
    evidence: list[str] = Field(default_factory=list)
