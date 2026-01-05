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
        # 파일이 없을 때를 대비한 기본값
        return {
            "rosy": {
                "name": "Rosy",
                "description": "a friendly staff",
                "style": "Be friendly.",
                "prefix": "Rosy: ",
                "temperature": 0.7,
            },
            "gordon": {
                "name": "Gordon",
                "description": "manager",
                "style": "Strict.",
                "prefix": "Gordon: ",
                "temperature": 0.2,
            },
        }

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

    # 🟢 [수정됨] 오분류 방지를 위한 강력한 가이드라인 적용
    prompt = f"""
You are the brain of a smart burger shop clerk.
Classify the user's message into EXACTLY ONE of these categories:

1. GREETING:
   - Social phrases only (Hi, Hello, Thanks, Bye, Good morning).
   - NO specific questions included.

2. MENU_QA:
   - Questions about food, taste, ingredients, price, or recommendations.
   - Questions about capabilities or usage ("What can I do?", "How do I order?", "Help").
   - Example: "What's good?", "What can I do here?"

3. STORE_INFO:
   - Facility info (Wi-Fi, Bathroom, Parking, Hours, Location).

4. ORDER:
   - Explicit intent to buy/add items.

5. HISTORY:
   - Asking about **PAST** orders ("What did I order?", "Receipt").
   - **CRITICAL**: "Hello", "Hi", "What can I do?" are NOT History. They are GREETING or MENU_QA.

6. COMPLAINT:
   - Negative feedback.

User Message: "{last_msg}"
Response (ONLY Category Name):"""

    # Router는 정확해야 하므로 temp=0.0 사용
    response = engine.generate_text(prompt, max_tokens=10, temperature=0.0)
    intent = response.strip().upper()

    if "HISTORY" in intent:
        final_intent = "history"
    elif "ORDER" in intent:
        final_intent = "order"
    elif "COMPLAINT" in intent:
        final_intent = "complaint"
    elif "GREETING" in intent:
        final_intent = "greeting"
    elif "MENU_QA" in intent:
        final_intent = "menu_qa"
    elif "STORE_INFO" in intent:
        final_intent = "store_info"
    else:
        # fallback to greeting/general if unsure
        final_intent = "greeting"

    print(
        f"🧭 [LLM Router] '{last_msg}' -> AI Thought: {intent} -> Final: {final_intent}"
    )

    return {"current_intent": final_intent}


def handle_order(state: AgentState):
    """주문 처리 -> Rosy (메뉴판만 검색)"""
    query = state["messages"][-1]["content"]
    print(f"🔍 [Agent] Verifying Order against Menu DB: '{query}'")

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

    # 방어 로직 1: 이전 대화가 아예 없으면 즉시 반환
    if len(past_messages) == 0:
        return {
            "final_response": f"{p['prefix']}You haven't ordered anything yet! 📝 How about trying our famous Gemma Classic? 🍔",
            "temperature": 0.7,
        }

    # 🟢 [수정됨] 옵션 제안 금지 및 빈 영수증 방지 프롬프트
    prompt = f"""
You are {p["name"]}, {p["description"]}.
Your Role: A burger shop clerk. (Do NOT act as a writing assistant).

Task: Check the conversation history below for CONFIRMED orders.

[Conversation]
{conversation_text}

[Rules]
1. LOOK CAREFULLY for items where the CLERK explicitly said "Confirmed" or "Added".
2. **IF** valid orders exist:
   - Output the receipt in the specified format:
     "{p["prefix"]}Here is your order so far! 🧾
     - [Quantity]x [Item Name] ($[Unit Price])
     ----------------
     Total: $[Total Price]
     Is this correct? 😊"
3. **IF NO** confirmed orders are found (or history only has greetings):
   - Respond strictly with: "{p["prefix"]}You haven't ordered anything yet! 📝 Feel free to ask about our menu or daily specials! 🍔"
4. **NEVER** provide options or suggestions on what the user should say. Just answer as Rosy.

Answer:"""

    return {"final_response": prompt, "temperature": 0.0}


def handle_greeting(state: AgentState):
    """인사 -> Rosy (RAG 없음)"""
    query = state["messages"][-1]["content"]

    prompt = build_prompt(
        persona_key="rosy",
        task_instruction="Just greet the customer warmly. DO NOT give menu info unless asked.",
        context_data="No external context needed.",
        user_query=query,
    )

    return {
        "final_response": prompt,
        "temperature": 0.7,
    }


def handle_menu_qa(state: AgentState):
    """메뉴 질문 -> Rosy (메뉴판 검색)"""
    query = state["messages"][-1]["content"]

    # 메뉴 정보만 필터링
    docs = rag_engine.search(query, filter={"type": "menu"})
    context = "\n".join(docs)

    prompt = build_prompt(
        persona_key="rosy",
        task_instruction="Explain the menu items, capabilities, or give recommendations based on the context.",
        context_data=context,
        user_query=query,
    )

    return {
        "final_response": prompt,
        "temperature": 0.5,
    }


def handle_store_info(state: AgentState):
    """시설 질문 -> Rosy (매장 정보 검색)"""
    query = state["messages"][-1]["content"]

    # 매장 정보만 필터링
    docs = rag_engine.search(query, filter={"type": "info"})
    context = "\n".join(docs)

    prompt = build_prompt(
        persona_key="rosy",
        task_instruction="Answer the customer's question about store facilities (WiFi, hours, etc).",
        context_data=context,
        user_query=query,
    )

    return {
        "final_response": prompt,
        "temperature": 0.2,
    }


# =============================================================================
# 4. Graph Construction
# =============================================================================

workflow = StateGraph(AgentState)

# 노드 등록
workflow.add_node("classify", classify_intent)
workflow.add_node("order_handler", handle_order)
workflow.add_node("complaint_handler", handle_complaint)
workflow.add_node("history_handler", handle_history)
workflow.add_node("greeting_handler", handle_greeting)
workflow.add_node("menu_qa_handler", handle_menu_qa)
workflow.add_node("store_info_handler", handle_store_info)

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
    elif intent == "greeting":
        return "greeting_handler"
    elif intent == "menu_qa":
        return "menu_qa_handler"
    elif intent == "store_info":
        return "store_info_handler"
    return "greeting_handler"


workflow.add_conditional_edges(
    "classify",
    route_intent,
    {
        "order_handler": "order_handler",
        "history_handler": "history_handler",
        "complaint_handler": "complaint_handler",
        "greeting_handler": "greeting_handler",
        "menu_qa_handler": "menu_qa_handler",
        "store_info_handler": "store_info_handler",
    },
)

# 종료 엣지 설정
workflow.add_edge("order_handler", END)
workflow.add_edge("complaint_handler", END)
workflow.add_edge("history_handler", END)
workflow.add_edge("greeting_handler", END)
workflow.add_edge("menu_qa_handler", END)
workflow.add_edge("store_info_handler", END)

# 체크포인터(메모리) 설정
memory = MemorySaver()
agent_app = workflow.compile(checkpointer=memory)
