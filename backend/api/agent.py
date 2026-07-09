import json
from typing import Any

from typing_extensions import NotRequired

from langchain.agents import create_agent
from langchain.agents.middleware import AgentState, before_agent
from langchain.messages import AIMessage
from langchain_core.messages import ToolMessage
from langgraph.runtime import Runtime
from langchain_google_genai import ChatGoogleGenerativeAI

from api.tools import diagnosis_tools


class DiagnosisState(AgentState):
    nickname: NotRequired[str]
    conversation: NotRequired[str]


@before_agent(state_schema=DiagnosisState, can_jump_to=["end"])
def check_answers_before_agent(
    state: DiagnosisState,
    runtime: Runtime,
) -> dict[str, Any] | None:
    print("===== before_agent =====")
    print(state["messages"][-1].content)

    conversation = state.get("conversation", "").strip()

    if not conversation:
        return {
            "messages": [
                AIMessage(content="진단할 대화 내용이 없습니다.")
            ],
            "jump_to": "end",
        }

    if len(conversation) < 100:
        return {
            "messages": [
                AIMessage(
                    content="진단을 진행하기에는 대화 내용이 충분하지 않습니다."
                )
            ],
            "jump_to": "end",
        }

    return None


llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0)

diagnosis_agent = create_agent(
    model=llm,
    tools=diagnosis_tools,
    middleware=[check_answers_before_agent],
    system_prompt="""
너는 RE:Bloom 진단 에이전트다.

반드시 아래 순서대로 작업한다.
1. `build_user_graph_data_tool`을 호출해 사용자 대화에서 진단용 그래프 데이터를 만든다.
2. 첫 번째 tool의 결과를 `save_user_graph_data_to_graph_tool`에 전달해 그래프 DB에 저장한다.
3. 마지막 tool의 JSON 결과만 반환한다.

단계를 건너뛰지 마라.
설명 문장 없이 최종 JSON만 반환하라.
""",
)


def run_diagnosis_agent(
    nickname: str,
    conversation: str,
):
    result = diagnosis_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"""
nickname: {nickname}

아래는 사용자와 나눈 전체 인터뷰 대화입니다.

{conversation}

이 대화를 바탕으로 진단 그래프 데이터를 만들고 저장하세요.
""",
                }
            ],
            "nickname": nickname,
            "conversation": conversation,
        }
    )

    tool_messages = [
        msg for msg in result["messages"]
        if isinstance(msg, ToolMessage)
    ]

    print("\n===== AGENT RESULT MESSAGES =====")
    for i, msg in enumerate(result["messages"]):
        print(f"\n--- message {i} ---")
        print("type:", type(msg))
        print("name:", getattr(msg, "name", None))
        print("content:", repr(getattr(msg, "content", None)))
        print("tool_calls:", getattr(msg, "tool_calls", None))

    print("\n===== TOOL MESSAGES ONLY =====")
    for i, msg in enumerate(tool_messages):
        print(f"\n--- tool message {i} ---")
        print("name:", getattr(msg, "name", None))
        print("content:", repr(msg.content))

    if not tool_messages:
        return {
            "nickname": nickname,
            "recovery_type": "",
            "strength_topics": [],
            "need_topics": [],
            "goal": "",
            "experience_tags": [],
            "summary": "",
            "scores": {},
            "graph_saved": False,
        }

    last_content = tool_messages[-1].content

    print("\n===== LAST TOOL CONTENT =====")
    print(repr(last_content))

    return json.loads(last_content)


chat_agent = create_agent(
    model=llm,
    tools=[],
    system_prompt="""
너는 RE:Bloom 진단 전 인터뷰를 위한 대화 에이전트다.

너의 역할은 최종 진단을 내리거나 해결책을 제안하는 것이 아니다.
사용자와 자연스럽게 대화하면서 이후 진단 단계에서 사용할 수 있는 정보를 수집하는 것이다.

최종적으로 아래 정보를 충분히 파악할 수 있을 만큼 대화를 진행한다.

- 최근 일상과 에너지 상태
- 취업 또는 진로에 대한 생각과 목표 직무
- 현재 준비 과정에서 어려운 부분
- 사용자가 스스로 강점이라고 느끼는 부분
- 이전 경험, 프로젝트, 아르바이트 등 활용 가능한 경험

대화 원칙은 아래와 같다.

1. 한 번에 질문은 하나만 한다.
2. 질문은 짧고 분명하게 한다.
3. 공감은 한 문장 이내로만 한다.
4. 같은 주제를 반복해서 깊게 묻지 않는다.
5. 사용자의 답이 너무 짧거나 모호할 때만 추가 질문을 한 번 더 한다.
6. recovery_type, summary, JSON 결과를 직접 만들지 않는다.
7. 사용자의 상태를 단정하지 않는다.
8. 해결책을 길게 제안하지 않는다.

대화는 보통 5~7턴 안에서 끝나도록 한다.
정보가 충분히 모였다고 판단되면 반드시 아래 문장만 그대로 출력한다.

"진단을 진행할게요."

말투는 자연스럽고 부담 없게 유지한다.
""",
)


def run_chat_agent(messages: list[dict]):
    result = chat_agent.invoke(
        {
            "messages": messages
        }
    )

    return result["messages"][-1].content
