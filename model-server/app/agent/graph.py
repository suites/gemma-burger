from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

# handlers에서 모든 핸들러 함수 임포트
from app.agent.handlers import (
    handle_complaint,
    handle_greeting,
    handle_history,
    handle_menu_qa,
    handle_order,
    handle_store_info,
)
from app.agent.router import classify_intent
from app.agent.state import AgentState

# 🟢 설정 주도형 매핑: 의도(Key)와 핸들러(Value) 연결
INTENT_MAP = {
    "order": handle_order,
    "history": handle_history,
    "complaint": handle_complaint,
    "greeting": handle_greeting,
    "menu_qa": handle_menu_qa,
    "store_info": handle_store_info,
}

workflow = StateGraph(AgentState)

# 1. Router 등록
workflow.add_node("classify", classify_intent)
workflow.set_entry_point("classify")

# 2. Handler 노드 자동 등록 (반복문 사용)
for key, func in INTENT_MAP.items():
    workflow.add_node(f"{key}_handler", func)
    workflow.add_edge(f"{key}_handler", END)


# 3. 라우팅 로직
def route_logic(state: AgentState):
    intent = state["current_intent"]
    # 매핑에 있으면 해당 핸들러, 없으면 greeting
    return f"{intent}_handler" if intent in INTENT_MAP else "greeting_handler"


# 4. 조건부 엣지 자동 등록
workflow.add_conditional_edges(
    "classify", route_logic, {f"{k}_handler": f"{k}_handler" for k in INTENT_MAP.keys()}
)

memory = MemorySaver()
agent_app = workflow.compile(checkpointer=memory)
