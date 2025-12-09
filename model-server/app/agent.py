import operator
from typing import Annotated, TypedDict, List
from langgraph.graph import StateGraph, END
from app.rag import rag_engine
from app.engine import engine

# 1. 상태(State) 정의
# 대화가 진행되는 동안 유지해야 할 데이터 구조입니다.
class AgentState(TypedDict):
    messages: List[dict]      # 대화 기록 (history)
    current_intent: str       # 현재 의도 (general, order)
    order_items: List[str]    # 장바구니
    final_response: str       # 사용자에게 보낼 응답

# 2. 노드(Node) 정의: 실제 작업을 수행하는 함수들

def classify_intent(state: AgentState):
    """사용자의 마지막 메시지를 보고 의도를 파악합니다."""
    last_user_msg = state["messages"][-1]["content"].lower()
    
    # (간단한 규칙 기반 분류 - 나중엔 LLM으로 대체 가능)
    if any(word in last_user_msg for word in ["order", "buy", "take", "want"]):
        return {"current_intent": "order"}
    elif any(word in last_user_msg for word in ["menu", "price", "what"]):
        return {"current_intent": "inquiry"}
    else:
        return {"current_intent": "general"}

def handle_general(state: AgentState):
    """일반 대화 및 메뉴 문의 처리 (RAG 사용)"""
    query = state["messages"][-1]["content"]
    
    print(f"🔍 [Agent] Searching RAG for: '{query}'")

    # RAG 검색
    docs = rag_engine.search(query)
    print(f"📄 [Agent] Retrieved {len(docs)} docs")
    
    context = "\n".join(docs)
    
    # 프롬프트 조립
    prompt = f"""
You are Gemma, a friendly staff at Gemma Burger.
Use the menu info to answer.

[Menu]
{context}

User: {query}
Answer:"""
    
    # (주의: 여기서는 스트리밍 대신 단순 생성을 사용하거나, 
    # 메인 로직에서 스트리밍을 하도록 프롬프트만 리턴할 수도 있습니다.
    # 여기서는 프롬프트를 완성해서 state에 넣는 방식을 씁니다.)
    return {"final_response": prompt} # 프롬프트 자체를 리턴하여 엔진이 돌리게 함

def handle_order(state: AgentState):
    """주문 처리 로직"""
    msg = state["messages"][-1]["content"]
    
    # (간단한 주문 추출 로직)
    # 실제로는 여기서 LLM에게 "주문 목록 추출해줘"라고 시킬 수 있습니다.
    
    prompt = f"""
You are taking an order. The customer said: "{msg}".
Reply enthusiastically and ask if they want anything else.
Current Order: {state.get('order_items', [])}

User: {msg}
Answer:"""
    return {"final_response": prompt}

# 3. 그래프(Workflow) 구성
workflow = StateGraph(AgentState)

# 노드 추가
workflow.add_node("classify", classify_intent)
workflow.add_node("general_handler", handle_general)
workflow.add_node("order_handler", handle_order)

# 시작점 설정
workflow.set_entry_point("classify")

# 조건부 엣지 (Router)
def route_intent(state: AgentState):
    intent = state["current_intent"]
    if intent == "order":
        return "order_handler"
    return "general_handler"

workflow.add_conditional_edges(
    "classify",
    route_intent,
    {
        "order_handler": "order_handler",
        "general_handler": "general_handler"
    }
)

# 끝점 설정
workflow.add_edge("general_handler", END)
workflow.add_edge("order_handler", END)

# 4. 컴파일 (실행 가능한 앱 생성)
agent_app = workflow.compile()