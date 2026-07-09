from langchain_core.tools import tool

from api.diagnosis_service import (
    build_user_graph_data,
    save_user_graph_data_to_graph,
)


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


diagnosis_tools = [
    build_user_graph_data_tool,
    save_user_graph_data_to_graph_tool,
]
