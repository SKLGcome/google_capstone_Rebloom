import json

from api.rag import indexer


def test_index_needs_rebuild_when_source_pdf_changes(tmp_path):
    documents_dir = tmp_path / "documents"
    index_dir = tmp_path / "index"
    documents_dir.mkdir()
    index_dir.mkdir()

    source = documents_dir / "mission.pdf"
    source.write_bytes(b"first version")
    (index_dir / "documents.json").write_text("[]", encoding="utf-8")
    (index_dir / "vectors.npz").write_bytes(b"index")
    (index_dir / "manifest.json").write_text(
        json.dumps(indexer.create_source_manifest(documents_dir)),
        encoding="utf-8",
    )

    assert indexer.mission_index_needs_rebuild(documents_dir, index_dir) is False

    source.write_bytes(b"second version")

    assert indexer.mission_index_needs_rebuild(documents_dir, index_dir) is True


def test_index_needs_rebuild_when_a_required_file_is_missing(tmp_path):
    documents_dir = tmp_path / "documents"
    index_dir = tmp_path / "index"
    documents_dir.mkdir()
    index_dir.mkdir()
    (documents_dir / "mission.pdf").write_bytes(b"source")

    assert indexer.mission_index_needs_rebuild(documents_dir, index_dir) is True
