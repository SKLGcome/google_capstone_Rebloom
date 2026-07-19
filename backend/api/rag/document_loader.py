"""미션 원본 문서를 불러와 청크로 분할한다."""

from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


BACKEND_DIR = Path(__file__).resolve().parents[2]
MISSION_DOCUMENTS_DIR = BACKEND_DIR / "data" / "mission_documents"

DEFAULT_CHUNK_SIZE = 250
DEFAULT_CHUNK_OVERLAP = 24


def load_and_split_pdf(
    file_path: str | Path,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Document]:
    """PDF 파일 하나를 불러와 서로 겹치는 청크로 분할한다."""

    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"Mission document not found: {path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Only .pdf documents are supported: {path}")

    if chunk_size < 1:
        raise ValueError("chunk_size must be at least 1")

    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be between 0 and chunk_size - 1")

    loader = PyPDFLoader(file_path=str(path))
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents=docs)

    for chunk_index, chunk in enumerate(chunks):
        chunk.metadata.update(
            {
                "source": str(path),
                "file_name": path.name,
                "chunk_index": chunk_index,
            }
        )

    return chunks


def load_mission_documents(
    documents_dir: str | Path = MISSION_DOCUMENTS_DIR,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Document]:
    """미션 문서 폴더의 모든 PDF를 불러와 청크로 분할한다."""

    directory = Path(documents_dir)

    if not directory.is_dir():
        raise FileNotFoundError(f"Mission documents directory not found: {directory}")

    chunks: list[Document] = []

    for file_path in sorted(directory.rglob("*.pdf")):
        chunks.extend(
            load_and_split_pdf(
                file_path=file_path,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        )

    return chunks
