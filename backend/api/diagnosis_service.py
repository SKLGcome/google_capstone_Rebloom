import json

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

import os
from dotenv import load_dotenv
from pathlib import Path

from langchain_neo4j import Neo4jGraph
from api.database import SessionLocal
from api.models import Diagnosis
from api.schemas import AnalysisResult, GraphProfileResult


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD"),
    database=os.getenv("NEO4J_DATABASE", "neo4j"),
)


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    temperature=0
)
structured_llm = llm.with_structured_output(AnalysisResult)


def analyze_answers(conversation: str):
    prompt = f"""
당신은 청년 회복 진단 전문가입니다.
아래 대화 내용을 종합적으로 분석하세요.
평가 기준:
- energy: 현재 신체적/정서적 에너지 수준
- direction: 진로·목표의 명확성
- action: 실제 행동으로 옮기는 정도
각 점수는 1~5점입니다.
대화 내용:{conversation}
"""

    result = structured_llm.invoke([
        SystemMessage(content="너는 청년 회복 진단을 수행하는 AI야."),
        HumanMessage(content=prompt)
    ])

    return result.model_dump()


def make_recovery_type(energy: int, direction: int, action: int):
    energy_code = "A" if energy >= 3 else "R"
    direction_code = "C" if direction >= 3 else "E"
    action_code = "D" if action >= 3 else "P"

    return f"{energy_code}{direction_code}{action_code}"

def get_recommendation_from_graph(recovery_type: str):
    result = graph.query(
        """
        MATCH (t:RecoveryType {id: $type})
        OPTIONAL MATCH (t)-[:RECOMMENDS]->(m:Mission)
        OPTIONAL MATCH (t)-[:NEXT_STEP]->(n:RecoveryType)
        RETURN 
            t.name AS typeName,
            collect(DISTINCT m.name) AS missions,
            n.id AS nextStep
        """,
        params={"type": recovery_type},
    )

    if not result:
        return {
            "typeName": None,
            "missions": [],
            "nextStep": None,
        }

    return result[0]


def save_diagnosis_to_db(user_id: int, recovery_type: str, summary: str):
    db = SessionLocal()

    try:
        diagnosis = Diagnosis(
            user_id=user_id,
            recovery_type=recovery_type,
            summary=summary,
        )

        db.add(diagnosis)
        db.commit()
        db.refresh(diagnosis)

        return {
            "id": diagnosis.id,
            "user_id": diagnosis.user_id,
            "recovery_type": diagnosis.recovery_type,
            "summary": diagnosis.summary,
        }

    finally:
        db.close()

profile_structured_llm = llm.with_structured_output(GraphProfileResult)


def extract_graph_profile(conversation: str):
    result = profile_structured_llm.invoke([
        SystemMessage(content="사용자 대화에서 그래프 DB 저장용 프로필 정보를 추출하는 AI입니다."),
        HumanMessage(content=f"""
다음 대화를 분석해서 아래 정보를 추출하세요.

- strength_topics: 사용자의 강점, 잘하는 것, 자신 있는 역량
- need_topics: 사용자가 보완해야 하거나 도움이 필요한 주제
- goal: 사용자의 목표 직무 또는 진로 목표
- experience_tags: 사용자가 겪은 주요 경험 태그

대화:
{conversation}
""")
    ])

    return result.model_dump()


def build_user_graph_data(nickname: str, conversation: str):
    analysis = analyze_answers(conversation)

    recovery_type = make_recovery_type(
        analysis["energy"],
        analysis["direction"],
        analysis["action"],
    )

    profile = extract_graph_profile(conversation)

    return {
        "nickname": nickname,
        "recovery_type": recovery_type,
        "strength_topics": profile["strength_topics"],
        "need_topics": profile["need_topics"],
        "goal": profile["goal"],
        "experience_tags": profile["experience_tags"],
        "summary": analysis["summary"],
        "scores": {
            "energy": analysis["energy"],
            "direction": analysis["direction"],
            "action": analysis["action"],
        },
    }


def save_user_graph_data_to_graph(graph_data: dict):
    scores = graph_data.get("scores", {})
    params = {
        "nickname": graph_data["nickname"],
        "recovery_type": graph_data["recovery_type"],
        "strength_topics": graph_data.get("strength_topics", []),
        "need_topics": graph_data.get("need_topics", []),
        "goal": graph_data.get("goal", ""),
        "experience_tags": graph_data.get("experience_tags", []),
        "summary": graph_data.get("summary", ""),
        "energy": scores.get("energy"),
        "direction": scores.get("direction"),
        "action": scores.get("action"),
    }

    graph.query(
        """
        MERGE (u:User {nickname: $nickname})
        SET
            u.recovery_type = $recovery_type,
            u.summary = $summary,
            u.energy = $energy,
            u.direction = $direction,
            u.action = $action,
            u.updated_at = datetime()

        CREATE (d:Diagnosis {
            recovery_type: $recovery_type,
            summary: $summary,
            energy: $energy,
            direction: $direction,
            action: $action,
            created_at: datetime()
        })
        MERGE (u)-[:HAS_DIAGNOSIS]->(d)

        WITH u
        OPTIONAL MATCH (u)-[r:HAS_RECOVERY_TYPE|HAS_STRENGTH|NEEDS|HAS_GOAL|HAS_EXPERIENCE]->()
        DELETE r
        """,
        params=params,
    )

    graph.query(
        """
        MATCH (u:User {nickname: $nickname})
        MERGE (rt:RecoveryType {id: $recovery_type})
        MERGE (u)-[:HAS_RECOVERY_TYPE]->(rt)
        """,
        params=params,
    )

    graph.query(
        """
        MATCH (u:User {nickname: $nickname})
        UNWIND $strength_topics AS topic_name
        WITH u, trim(topic_name) AS topic_name
        WHERE topic_name <> ""
        MERGE (t:Topic {name: topic_name})
        MERGE (u)-[:HAS_STRENGTH]->(t)
        """,
        params=params,
    )

    graph.query(
        """
        MATCH (u:User {nickname: $nickname})
        UNWIND $need_topics AS topic_name
        WITH u, trim(topic_name) AS topic_name
        WHERE topic_name <> ""
        MERGE (t:Topic {name: topic_name})
        MERGE (u)-[:NEEDS]->(t)
        """,
        params=params,
    )

    graph.query(
    """
    MATCH (u:User {nickname: $nickname})
    MATCH (rt:RecoveryType {id: $recovery_type})
    MERGE (room:ChatRoom {room_id: "type_" + rt.id})
    SET room.name = coalesce(rt.name, rt.id) + " 방",
        room.kind = "TYPE"
    MERGE (room)-[:FOR_TYPE]->(rt)
    MERGE (u)-[:JOINED]->(room)
    RETURN room.room_id AS room_id, room.name AS room_name
    """,
    params=params,
    )

    graph.query(
        """
        MATCH (u:User {nickname: $nickname})
        WITH u, trim($goal) AS goal_name
        WHERE goal_name <> ""
        MERGE (g:Goal {name: goal_name})
        MERGE (u)-[:HAS_GOAL]->(g)
        """,
        params=params,
    )

    graph.query(
        """
        MATCH (u:User {nickname: $nickname})
        UNWIND $experience_tags AS experience_name
        WITH u, trim(experience_name) AS experience_name
        WHERE experience_name <> ""
        MERGE (e:Experience {name: experience_name})
        MERGE (u)-[:HAS_EXPERIENCE]->(e)
        """,
        params=params,
    )

    return {
        **graph_data,
        "graph_saved": True,
    }


def build_and_save_user_graph_data(nickname: str, conversation: str):
    graph_data = build_user_graph_data(nickname, conversation)
    return save_user_graph_data_to_graph(graph_data)
