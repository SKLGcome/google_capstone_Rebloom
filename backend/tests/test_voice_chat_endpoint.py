import os
import sys
import types

os.environ.setdefault("NEO4J_URI", "bolt://localhost:7687")
os.environ.setdefault("NEO4J_USERNAME", "neo4j")
os.environ.setdefault("NEO4J_PASSWORD", "password")

if "langchain_neo4j" not in sys.modules:
    langchain_neo4j_stub = types.ModuleType("langchain_neo4j")

    class DummyNeo4jGraph:
        def __init__(self, *args, **kwargs):
            pass

    langchain_neo4j_stub.Neo4jGraph = DummyNeo4jGraph
    sys.modules["langchain_neo4j"] = langchain_neo4j_stub

from api.main import app


def test_voice_chat_route_exists():
    assert any(route.path == "/chat/voice" for route in app.routes)
