import operator
from typing import Annotated, TypedDict, List, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver # ⬅️ [추가] 메모리 저장소
from app.rag import rag_engine
from app.engine import engine

# 1. 상태(State) 정의 수정
class AgentState(TypedDict):
    # 🟢 [수정] messages에 'operator.add'를 적용하여 리스트가 계속 쌓이게 만듭니다.
    messages: Annotated[List[dict], operator.add]
    current_intent: str
    final_response: str

# 2. 노드(Node) 정의 (기존과 거의 동일하지만, 메시지 참조 방식이 조금 바뀝니다)

# model-server/app/agent.py

def classify_intent(state: AgentState):
    """LLM을 사용하여 사용자의 발화 의도(Intent)를 분류합니다."""
    last_msg = state["messages"][-1]["content"]
    
    # 🟢 [수정] 프롬프트 강화: ORDER와 GENERAL(INQUIRY)의 경계를 명확히 설정
    prompt = f"""
You are an intent classifier for a burger shop chatbot.
Analyze the User Message and classify it into ONE of the following categories:

1. HISTORY:
   - User asks about previous orders, bill, receipt, or "what did I order?".

2. ORDER:
   - User explicitly wants to ADD a specific item to the cart NOW.
   - Examples: "Add a burger", "I'll take the classic one", "One shake please", "Yes, add it".
   - KEY: The user has made a decision.

3. GENERAL:
   - User expresses a preference, asks for recommendations, or asks questions.
   - User says "I want..." but hasn't picked a specific item yet.
   - Examples: "I want something cheesy", "Do you have vegan food?", "I'm hungry", "What is the price?".
   - KEY: The user is still deciding or consulting.

User Message: "{last_msg}"

Response (ONLY output the category name: HISTORY, ORDER, or GENERAL):"""

    # ... (이하 LLM 호출 코드는 동일) ...
    response = engine.generate_text(prompt, max_tokens=10, temperature=0.0)
    intent = response.strip().upper()
    
    # 파싱 및 리턴 로직 (기존과 동일)
    if "HISTORY" in intent:
        final_intent = "history"
    elif "ORDER" in intent:
        final_intent = "order"
    else:
        final_intent = "general" # 상담/문의 (RAG)
        
    print(f"🧭 [LLM Router] '{last_msg}' -> AI Thought: {intent} -> Final: {final_intent}")
    
    return {"current_intent": final_intent}

def handle_history(state: AgentState):
    """대화 기록(Memory)을 보고 주문 내역을 요약"""
    
    # 1. 대화 기록 포맷팅
    history_lines = []
    # 현재 질문(마지막 메시지)을 제외한 이전 대화가 있는지 확인하기 위해 분리
    past_messages = state["messages"][:-1] 
    
    for msg in state["messages"]:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if role == "user":
            history_lines.append(f"CUSTOMER: {content}")
        elif role == "assistant":
            history_lines.append(f"CLERK: {content}")
            
    conversation_text = "\n".join(history_lines)
    print(f"📜 [History Context] (Length: {len(state['messages'])})\n{conversation_text}\n" + "-"*20)

    # 🛡️ [방어 로직] 핵심: 이전 대화가 없으면 AI 호출 없이 바로 리턴
    # 메시지가 1개(방금 질문한 것) 뿐이라면 주문 내역이 있을 수 없음.
    if len(past_messages) == 0:
        print("⚡️ [Logic] No history found. Skipping LLM generation.")
        return {"final_response": "You haven't ordered anything yet! 📝 Feel free to check our menu."}

    # 2. 프롬프트 작성 (기존과 동일하지만, 규칙 강화)
    prompt = f"""
Role: You are a strict cashier.
Task: List ordered food items based ONLY on the conversation below.

[Conversation]
{conversation_text}

[Rules]
1. If NO food items were confirmed by the CLERK, say "No orders found".
2. Do NOT invent or hallucinate items.
3. Ignore the user's last question asking for the bill.
4. Output format: "You ordered: [Item] ($Price)... Total: $X"

Answer:"""
    
    return {"final_response": prompt}

def handle_general(state: AgentState):
    query = state["messages"][-1]["content"]
    
    print(f"🔍 [Agent] Searching RAG for: '{query}'")
    docs = rag_engine.search(query)
    context = "\n".join(docs)
    
    # 🟢 [팁] 이전 대화 내용을 프롬프트에 포함시키고 싶다면 state["messages"]를 활용할 수 있습니다.
    # 여기서는 간단히 RAG만 수행합니다.
    
    prompt = f"""
You are Gemma, a friendly staff at Gemma Burger.
Use the menu info to answer.

[Menu]
{context}

User: {query}
Answer:"""
    return {"final_response": prompt}

def handle_order(state: AgentState):
    """주문 의도 감지 -> RAG 검색 -> 메뉴 검증 및 접수"""
    query = state["messages"][-1]["content"]
    
    print(f"🔍 [Agent] Verifying Order against Menu: '{query}'")
    docs = rag_engine.search(query)
    context = "\n".join(docs)
    
    prompt = f"""
You are Gemma, a smart waiter.
The customer wants to order: "{query}".

Check the [Menu Info] below.
1. If the user asks for a generic name (e.g., "cheese burger"), match it to the closest item on the menu (e.g., "The Gemma Classic").
2. Confirm the order using the OFFICIAL menu item name and price.
3. If the item is not on the menu at all, apologize and suggest something else.
4. Use emojis! 🍔

[Menu Info]
{context}

Customer: {query}
Answer:"""
    
    return {"final_response": prompt}

# 3. 그래프 구성
workflow = StateGraph(AgentState)

workflow.add_node("classify", classify_intent)
workflow.add_node("general_handler", handle_general)
workflow.add_node("order_handler", handle_order)
workflow.add_node("history_handler", handle_history)

workflow.set_entry_point("classify")

def route_intent(state: AgentState):
    intent = state["current_intent"]
    print(f"🔍 [Agent] Intent: {intent}")
    if intent == "order":
        return "order_handler"
    elif intent == "history":  # ⬅️ [추가]
        return "history_handler"
    return "general_handler"

workflow.add_conditional_edges("classify", route_intent)
workflow.add_edge("general_handler", END)
workflow.add_edge("order_handler", END)
workflow.add_edge("history_handler", END)

# 4. 🟢 [수정] 컴파일 시 체크포인터(메모리) 추가
memory = MemorySaver()
agent_app = workflow.compile(checkpointer=memory)