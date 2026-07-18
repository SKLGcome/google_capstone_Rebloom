from langchain_core.tools import tool

from api.diagnosis.service import (
    build_user_graph_data,
    save_user_graph_data_to_graph,
)
from api.missions.service import load_all_type_contexts


@tool
def build_user_graph_data_tool(nickname: str, conversation: str) -> dict:
    """
    Build structured diagnosis graph data from the user's conversation.
    Use this first.
    """
    return build_user_graph_data(nickname, conversation)


@tool
def save_user_graph_data_to_graph_tool(graph_data: dict) -> dict:
    """
    Save the structured diagnosis graph data to Neo4j.
    Use this only after build_user_graph_data_tool.
    """
    return save_user_graph_data_to_graph(graph_data)


@tool
def retrieve_community_contexts_tool(
    hours: int = 48,
    limit_per_type: int = 100,
) -> dict[str, list[dict]]:
    """Retrieve community context for daily mission generation.

    Use this tool before generating missions. It returns recent community
    messages for all eight recovery types, grouped by recovery type code.
    `hours` is clamped to 1-168 and `limit_per_type` to 1-200.

    Example output:
    {
        "REP": [{"content": "..."}],
        "RED": [{"content": "..."}],
        ...
    }
    """
    return load_all_type_contexts(
        hours=hours,
        limit_per_type=limit_per_type,
    )


diagnosis_tools = [
    build_user_graph_data_tool,
    save_user_graph_data_to_graph_tool,
]


mission_tools = [
    retrieve_community_contexts_tool,
]
