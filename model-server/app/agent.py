import operator
import os
from typing import Annotated, List, TypedDict

import yaml
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from app.engine import engine
from app.rag import rag_engine

# =============================================================================
# 1. Configuration & Utils (Persona Management)
# =============================================================================


def load_personas():
    """resources/personas.yaml 파일에서 에이전트 페르소나 설정을 로드합니다."""
    base_path = os.path.dirname(__file__)
    yaml_path = os.path.join(base_path, "../../resources/personas.yaml")

    if not os.path.exists(yaml_path):
        print(f"⚠️ Warning: Personas file not found at {yaml_path}. Using default.")
        raise FileNotFoundError(f"Personas file not found at {yaml_path}")

    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# 앱 시작 시 페르소나 로드
PERSONA_CONFIG = load_personas()
print(f"✨ Loaded personas: {list(PERSONA_CONFIG.keys())}")


def build_prompt(
    persona_key: str, task_instruction: str, context_data: str, user_query: str = ""
) -> str:
    """공통 프롬프트 빌더: 페르소나 키에 맞춰 시스템 프롬프트를 조립합니다."""
    p = PERSONA_CONFIG.get(persona_key)
    if not p:
        p = PERSONA_CONFIG["rosy"]  # Fallback

    return f"""
You are {p["name"]}, {p["description"]}.
{task_instruction}

[Context/Info]
{context_data}

[Rules]
1. {p["style"]}
2. ALWAYS start your response with "{p["prefix"]}".

User Query: {user_query}
Answer:"""


# =============================================================================
# 2. State Definition
# =============================================================================


class AgentState(TypedDict):
    # messages: 대화 내역 (operator.add를 통해 리스트가 계속 누적됨)
    messages: Annotated[List[dict], operator.add]
    current_intent: str
    final_response: str
    temperature: float  # 에이전트별 창의성 조절을 위한 파라미터


# =============================================================================
# 3. Nodes (Agent Logic)
# =============================================================================


def classify_intent(state: AgentState):
    """LLM Router: 사용자의 의도를 분석하여 적절한 핸들러로 분배합니다."""
    last_msg = state["messages"][-1]["content"]

    # Few-shot Prompting for Classification
    prompt = f"""
You are an intent classifier for a burger shop chatbot.
Classify the user's message into ONE of the following categories:

1. HISTORY:
   - User asks about previous orders, bill, receipt, or "what did I order?".

2. ORDER:
   - User explicitly wants to ADD a specific item to the cart NOW (e.g., "I want a burger", "Add fries").
   - User has made a decision.

3. COMPLAINT:
   - User expresses dissatisfaction, anger, or asks for a manager/refund.
   - Keywords: "bad", "cold", "refund", "manager", "hate", "slow".

4. GENERAL:
   - User asks about menu, price, location, or just says "I want something..." without picking a specific item.
   - Greetings or general questions.

User Message: "{last_msg}"

Response (ONLY output the category name: HISTORY, ORDER, COMPLAINT, or GENERAL):"""

    # Router는 창의성이 필요 없으므로 temp=0.0 사용
    response = engine.generate_text(prompt, max_tokens=10, temperature=0.0)
    intent = response.strip().upper()

    if "HISTORY" in intent:
        final_intent = "history"
    elif "ORDER" in intent:
        final_intent = "order"
    elif "COMPLAINT" in intent:
        final_intent = "complaint"
    else:
        final_intent = "general"

    print(
        f"🧭 [LLM Router] '{last_msg}' -> AI Thought: {intent} -> Final: {final_intent}"
    )

    return {"current_intent": final_intent}


def handle_general(state: AgentState):
    """일반 대화 -> Rosy (전체 검색)"""
    query = state["messages"][-1]["content"]

    # 일반 질문은 전체 정보(메뉴+매장정보) 검색
    docs = rag_engine.search(query)
    context = "\n".join(docs)

    prompt = build_prompt(
        persona_key="rosy",
        task_instruction="Answer the customer's question based ONLY on the info below.",
        context_data=context,
        user_query=query,
    )

    return {
        "final_response": prompt,
        "temperature": PERSONA_CONFIG["rosy"]["temperature"],
    }


def handle_order(state: AgentState):
    """주문 처리 -> Rosy (메뉴판만 검색)"""
    query = state["messages"][-1]["content"]
    print(f"🔍 [Agent] Verifying Order against Menu DB: '{query}'")

    # 주문 시에는 'type: menu' 데이터만 필터링하여 검색
    docs = rag_engine.search(query, filter={"type": "menu"})
    context = "\n".join(docs)

    task = """
The customer wants to order. Match the request to the OFFICIAL menu item name.
1. If found, accept the order and confirm the price.
2. If NOT found, apologize and suggest available items.
    """

    prompt = build_prompt(
        persona_key="rosy",
        task_instruction=task,
        context_data=context,
        user_query=query,
    )

    return {
        "final_response": prompt,
        "temperature": PERSONA_CONFIG["rosy"]["temperature"],
    }


def handle_complaint(state: AgentState):
    """불만 접수 -> Gordon (규정 검색)"""
    query = state["messages"][-1]["content"]
    print("🚨 [Agent] Complaint detected! Switching to Manager Gordon.")

    # 규정(Policy) 정보 검색 (type: info)
    docs = rag_engine.search(query, filter={"type": "info"})
    context = "\n".join(docs)

    prompt = build_prompt(
        persona_key="gordon",
        task_instruction="Review the [Store Policy] below and respond professionally to the complaint.",
        context_data=context,
        user_query=query,
    )

    return {
        "final_response": prompt,
        "temperature": PERSONA_CONFIG["gordon"]["temperature"],
    }


def handle_history(state: AgentState):
    """주문 내역 확인 -> Rosy (계산 및 요약)"""
    # 1. 대화 기록 포맷팅
    history_lines = []
    # 현재 질문을 제외한 과거 기록 확인
    past_messages = state["messages"][:-1]

    for msg in state["messages"]:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if role == "user":
            history_lines.append(f"CUSTOMER: {content}")
        elif role == "assistant":
            history_lines.append(f"CLERK: {content}")

    conversation_text = "\n".join(history_lines)
    print(
        f"📜 [History Context] (Length: {len(state['messages'])})\n{conversation_text}\n"
        + "-" * 20
    )

    p = PERSONA_CONFIG["rosy"]

    # 방어 로직: 이전 대화가 없으면 즉시 반환
    if len(past_messages) == 0:
        return {
            "final_response": f"{p['prefix']}You haven't ordered anything yet! 📝 How about trying our famous Gemma Classic? 🍔",
            "temperature": 0.7,
        }

    # 2. 요약 프롬프트
    prompt = f"""
You are {p["name"]}, {p["description"]}.
Task: Summarize the customer's order based ONLY on the history below.

[Conversation]
{conversation_text}

[Rules]
1. List only confirmed items (where CLERK said yes).
2. ALWAYS start your response with "{p["prefix"]}".
3. Output format example:
   "{p["prefix"]}Here is your order so far! 🧾
   - [Quantity]x [Item Name] ($[Unit Price])
   ----------------
   Total: $[Total Price]
   Is this correct? 😊"

Answer:"""

    # 계산 및 요약은 정확해야 하므로 temperature=0.0
    return {"final_response": prompt, "temperature": 0.0}


# =============================================================================
# 4. Graph Construction
# =============================================================================

workflow = StateGraph(AgentState)

# 노드 등록
workflow.add_node("classify", classify_intent)
workflow.add_node("general_handler", handle_general)
workflow.add_node("order_handler", handle_order)
workflow.add_node("complaint_handler", handle_complaint)
workflow.add_node("history_handler", handle_history)

# 시작점 설정
workflow.set_entry_point("classify")


# 조건부 엣지 (Router Logic)
def route_intent(state: AgentState):
    intent = state["current_intent"]
    if intent == "order":
        return "order_handler"
    elif intent == "history":
        return "history_handler"
    elif intent == "complaint":
        return "complaint_handler"
    return "general_handler"


workflow.add_conditional_edges(
    "classify",
    route_intent,
    {
        "order_handler": "order_handler",
        "history_handler": "history_handler",
        "complaint_handler": "complaint_handler",
        "general_handler": "general_handler",
    },
)

# 종료 엣지 설정
workflow.add_edge("general_handler", END)
workflow.add_edge("order_handler", END)
workflow.add_edge("complaint_handler", END)
workflow.add_edge("history_handler", END)

# 체크포인터(메모리) 설정
memory = MemorySaver()
agent_app = workflow.compile(checkpointer=memory)
