"""벡터·키워드 검색과 가중치 RRF로 미션 컨텍스트를 검색한다."""

import json
import math
import re
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np
from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.retrievers import BaseRetriever
from pydantic import ConfigDict, Field

from api.rag.indexer import (
    DOCUMENT_INDEX_PATH,
    MISSION_INDEX_DIR,
    VECTOR_INDEX_PATH,
    get_embedding_model,
)


_TOKEN_PATTERN = re.compile(r"[가-힣]+|[a-zA-Z]+|\d+")


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_PATTERN.findall(text)]


def _matches_metadata(document: Document, filters: Mapping[str, Any]) -> bool:
    return all(document.metadata.get(key) == value for key, value in filters.items())


class LocalVectorRetriever(BaseRetriever):
    """로컬 NumPy 인덱스에서 코사인 유사도로 검색한다."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    documents: list[Document]
    vectors: np.ndarray
    embeddings: Embeddings
    k: int = 10
    metadata_filter: dict[str, Any] = Field(default_factory=dict)

    def _get_relevant_documents(self, query: str, *, run_manager: Any) -> list[Document]:
        query_vector = np.asarray(self.embeddings.embed_query(query), dtype=np.float32)
        if query_vector.ndim != 1 or query_vector.shape[0] != self.vectors.shape[1]:
            raise RuntimeError("Query embedding dimension does not match the vector index")

        vector_norms = np.linalg.norm(self.vectors, axis=1)
        query_norm = float(np.linalg.norm(query_vector))
        denominator = vector_norms * query_norm
        scores = np.divide(
            self.vectors @ query_vector,
            denominator,
            out=np.full(len(self.vectors), -np.inf, dtype=np.float32),
            where=denominator != 0,
        )
        candidates = (
            index for index in np.argsort(scores)[::-1]
            if _matches_metadata(self.documents[index], self.metadata_filter)
        )
        return [self.documents[index] for index in list(candidates)[: self.k]]


class KeywordRetriever(BaseRetriever):
    """외부 검색 의존성 없이 BM25 방식으로 키워드를 검색한다."""

    documents: list[Document]
    k: int = 10
    metadata_filter: dict[str, Any] = Field(default_factory=dict)
    tokenized_documents: list[list[str]] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        if not self.tokenized_documents:
            self.tokenized_documents = [_tokenize(doc.page_content) for doc in self.documents]

    def _get_relevant_documents(self, query: str, *, run_manager: Any) -> list[Document]:
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        eligible = [
            index for index, document in enumerate(self.documents)
            if _matches_metadata(document, self.metadata_filter)
        ]
        if not eligible:
            return []

        document_frequency = Counter(
            token for index in eligible for token in set(self.tokenized_documents[index])
        )
        average_length = sum(len(self.tokenized_documents[i]) for i in eligible) / len(eligible)
        scored: list[tuple[float, int]] = []
        for index in eligible:
            tokens = self.tokenized_documents[index]
            frequencies = Counter(tokens)
            score = 0.0
            for token in query_tokens:
                frequency = frequencies[token]
                if not frequency:
                    continue
                df = document_frequency[token]
                idf = math.log(1 + (len(eligible) - df + 0.5) / (df + 0.5))  ## 다른 문서에는 없는 희귀도 측정
                length_normalizer = frequency + 1.5 * (
                    1 - 0.75 + 0.75 * len(tokens) / max(average_length, 1)   ## 길이 보정
                )
                score += idf * frequency * 2.5 / length_normalizer
            if score > 0:
                scored.append((score, index))

        scored.sort(reverse=True)
        return [self.documents[index] for _, index in scored[: self.k]]


def load_local_index(index_dir: str | Path = MISSION_INDEX_DIR) -> tuple[list[Document], np.ndarray]:
    """indexer.py가 생성한 문서와 벡터 파일을 불러와 검증한다."""

    directory = Path(index_dir)
    document_path = directory / DOCUMENT_INDEX_PATH.name
    vector_path = directory / VECTOR_INDEX_PATH.name
    records = json.loads(document_path.read_text(encoding="utf-8"))
    documents = [
        Document(page_content=record["page_content"], metadata=record.get("metadata", {}))
        for record in records
    ]
    with np.load(vector_path) as archive:
        vectors = np.asarray(archive["vectors"], dtype=np.float32)

    if vectors.ndim != 2 or len(vectors) != len(documents):
        raise RuntimeError("Vector and document indexes are out of sync")
    return documents, vectors


def build_hybrid_retriever(
    index_dir: str | Path = MISSION_INDEX_DIR,
    *,
    embeddings: Embeddings | None = None,
    k: int = 10,
    vector_weight: float = 0.7,
    keyword_weight: float = 0.4,
    rrf_c: int = 60,
    metadata_filter: Mapping[str, Any] | None = None,
) -> EnsembleRetriever:
    """벡터·키워드 검색 순위를 RRF로 결합하는 LangChain 앙상블을 생성한다."""

    if k < 1:
        raise ValueError("k must be at least 1")
    if vector_weight < 0 or keyword_weight < 0 or vector_weight + keyword_weight <= 0:
        raise ValueError("retriever weights must be non-negative and not both zero")
    if rrf_c < 0:
        raise ValueError("rrf_c must be non-negative")

    documents, vectors = load_local_index(index_dir)
    filters = dict(metadata_filter or {})
    vector_retriever = LocalVectorRetriever(
        documents=documents,
        vectors=vectors,
        embeddings=embeddings or get_embedding_model(task_type="RETRIEVAL_QUERY"),
        k=k,
        metadata_filter=filters,
    )
    keyword_retriever = KeywordRetriever(
        documents=documents,
        k=k,
        metadata_filter=filters,
    )
    return EnsembleRetriever(
        retrievers=[vector_retriever, keyword_retriever],
        weights=[vector_weight, keyword_weight],
        c=rrf_c,
    )


def retrieve_mission_documents(
    query: str,
    *,
    k: int = 8,
    retriever: BaseRetriever | None = None,
) -> list[Document]:
    """미션 query로 문서를 검색해 evaluator가 받을 Document 목록을 반환한다.

    ``retriever`` 주입은 테스트와 애플리케이션 수준 캐싱에 사용할 수 있다.
    주입하지 않으면 로컬 인덱스로 하이브리드 Retriever를 생성한다.
    """

    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("query must not be empty")
    if k < 1:
        raise ValueError("k must be at least 1")

    active_retriever = retriever or build_hybrid_retriever(k=k)
    documents = active_retriever.invoke(normalized_query)
    return list(documents)[:k]
