"""미션 문서의 벡터 인덱스를 생성하고 저장한다."""

import json
import os
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pydantic import SecretStr

from api.rag.document_loader import BACKEND_DIR, load_mission_documents


load_dotenv(BACKEND_DIR / ".env")

MISSION_INDEX_DIR = BACKEND_DIR / "data" / "mission_index"
VECTOR_INDEX_PATH = MISSION_INDEX_DIR / "vectors.npz"
DOCUMENT_INDEX_PATH = MISSION_INDEX_DIR / "documents.json"

DEFAULT_EMBEDDING_MODEL = "models/gemini-embedding-001"
DEFAULT_BATCH_SIZE = 100


def get_embedding_model(
    task_type: str = "RETRIEVAL_DOCUMENT",
) -> GoogleGenerativeAIEmbeddings:
    """문서 인덱싱 또는 질의 검색에 사용할 임베딩 클라이언트를 생성한다."""

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required to build the mission index")

    return GoogleGenerativeAIEmbeddings(
        model=os.getenv("GEMINI_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
        api_key=SecretStr(api_key),
        task_type=task_type,
    )


def _serialize_documents(documents: list[Document]) -> list[dict]:
    """LangChain 문서를 JSON으로 직렬화할 수 있는 레코드로 변환한다."""

    return [
        {
            "page_content": document.page_content,
            "metadata": document.metadata,
        }
        for document in documents
    ]


def build_mission_index(
    documents: list[Document] | None = None,
    index_dir: str | Path = MISSION_INDEX_DIR,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> dict:
    """미션 문서 청크를 임베딩하고 로컬 벡터 인덱스로 저장한다.

    ``documents``를 생략하면 미션 문서 디렉터리의 모든 PDF를 먼저
    불러와 청크로 분할한다.
    """

    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")

    chunks = documents if documents is not None else load_mission_documents()

    if not chunks:
        raise ValueError("No mission document chunks were found to index")

    embedding_model = get_embedding_model()
    texts = [chunk.page_content for chunk in chunks]
    vectors = embedding_model.embed_documents(
        texts,
        batch_size=batch_size,
    )
    vector_array = np.asarray(vectors, dtype=np.float32)

    if vector_array.ndim != 2 or len(vector_array) != len(chunks):
        raise RuntimeError("Embedding output does not match the document chunks")

    target_dir = Path(index_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    vector_path = target_dir / VECTOR_INDEX_PATH.name
    document_path = target_dir / DOCUMENT_INDEX_PATH.name

    np.savez_compressed(vector_path, vectors=vector_array)
    document_path.write_text(
        json.dumps(_serialize_documents(chunks), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "document_count": len(chunks),
        "embedding_dimension": int(vector_array.shape[1]),
        "embedding_model": embedding_model.model,
        "vector_index_path": str(vector_path),
        "document_index_path": str(document_path),
    }
