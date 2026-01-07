import json

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

# handlers에서 모든 핸들러 함수 임포트
from app.agent.handlers import (
    handle_cancel,
    handle_complaint,
    handle_greeting,
    handle_history,
    handle_menu_qa,
    handle_order,
    handle_remove,
    handle_store_info,
)
from app.agent.router import classify_intent
from app.agent.state import AgentState, Intent
from app.agent.utils import PROMPTS
from app.engine import engine
from app.rag import rag_engine

# 🟢 설정 주도형 매핑: 의도(Enum)와 핸들러(Value) 연결
INTENT_MAP = {
    Intent.ORDER.value: handle_order,
    Intent.HISTORY.value: handle_history,
    Intent.COMPLAINT.value: handle_complaint,
    Intent.GREETING.value: handle_greeting,
    Intent.MENU_QA.value: handle_menu_qa,
    Intent.STORE_INFO.value: handle_store_info,
    Intent.CANCEL.value: handle_cancel,
    Intent.REMOVE.value: handle_remove,
}

workflow = StateGraph(AgentState)

# 1. Router 등록
workflow.add_node("classify", classify_intent)
workflow.set_entry_point("classify")


def extract_cart_update(state: AgentState):
    messages = state["messages"]
    query = messages[-1]["content"]

    prev_ai_msg = ""
    if len(messages) >= 2:
        prev_ai_msg = messages[-2]["content"]

    search_query = f"{prev_ai_msg} {query}" if prev_ai_msg else query
    docs = rag_engine.search(search_query, filter={"type": "menu"}, k=10)
    menu_context = "\n".join(docs)

    prompt_template = PROMPTS["extraction"]["task"]
    extraction_prompt = prompt_template.format(
        menu_context=menu_context, prev_ai_msg=prev_ai_msg, user_query=query
    )

    response = engine.generate_text(extraction_prompt, max_tokens=100, temperature=0.0)

    try:
        start = response.find("[")
        end = response.rfind("]") + 1
        if start != -1 and end != -1:
            new_items = json.loads(response[start:end])
            if isinstance(new_items, list):
                return {"cart": new_items}
    except Exception as e:
        print(f"⚠️ Cart Extraction Failed: {e}")

    return {"cart": []}


workflow.add_node("extract_cart", extract_cart_update)


# 2. Handler 노드 자동 등록 (반복문 사용)
for key, func in INTENT_MAP.items():
    workflow.add_node(f"{key}_handler", func)
    workflow.add_edge(f"{key}_handler", END)


# 3. 라우팅 로직
def route_logic(state: AgentState):
    intent = state["current_intent"]
    if intent in [Intent.ORDER.value, Intent.REMOVE.value]:
        return "extract_cart"

    return (
        f"{intent}_handler"
        if intent in INTENT_MAP
        else f"{Intent.GREETING.value}_handler"
    )


workflow.add_edge("extract_cart", f"{Intent.ORDER.value}_handler")


# 4. 조건부 엣지 자동 등록
path_map: dict = {f"{k}_handler": f"{k}_handler" for k in INTENT_MAP.keys()}
path_map["extract_cart"] = "extract_cart"

workflow.add_conditional_edges("classify", route_logic, path_map)

memory = MemorySaver()
agent_app = workflow.compile(checkpointer=memory)
