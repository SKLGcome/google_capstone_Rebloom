import json

import numpy as np
from langchain_core.embeddings import Embeddings
from langchain_core.messages import AIMessage

from api.rag.query_builder import build_retrieval_query
from api.rag.retriever import build_hybrid_retriever


class FakeEmbeddings(Embeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return [1.0, 0.0] if "산책" in text else [0.0, 1.0]


class FakeSummaryLlm:
    def invoke(self, messages):
        assert "가벼운 산책" in messages[-1].content
        return AIMessage(content="부담 없이 할 수 있는 가벼운 산책을 선호한다.")


def test_build_retrieval_query_accepts_message_records():
    query = build_retrieval_query(
        "rep",
        [{"content": "가벼운 산책"}, {"content": "  "}],
        llm=FakeSummaryLlm(),
    )

    assert "회복 유형: REP" in query
    assert "부담 없이 할 수 있는 가벼운 산책을 선호한다." in query


def test_hybrid_retriever_uses_local_indexes(tmp_path):
    records = [
        {"page_content": "오늘은 가벼운 산책을 해보세요", "metadata": {"type": "REP"}},
        {"page_content": "조용히 음악을 감상하세요", "metadata": {"type": "REP"}},
    ]
    (tmp_path / "documents.json").write_text(json.dumps(records), encoding="utf-8")
    np.savez_compressed(tmp_path / "vectors.npz", vectors=np.array([[1, 0], [0, 1]], dtype=np.float32))

    retriever = build_hybrid_retriever(tmp_path, embeddings=FakeEmbeddings(), k=2)
    results = retriever.invoke("산책")

    assert results[0].page_content == records[0]["page_content"]
