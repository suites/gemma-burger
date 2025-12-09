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
    
    # 1. 대화 기록 포맷팅 (기존과 동일)
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
    print(f"📜 [History Context] (Length: {len(state['messages'])})\n{conversation_text}\n" + "-"*20)

    # 🛡️ [방어 로직] 아예 대화가 없을 때
    if len(past_messages) == 0:
        return {"final_response": "You haven't ordered anything yet! 📝 How about trying our famous Gemma Classic? 🍔"}

    # 2. 🟢 [수정] 프롬프트 개선: 수량과 가격 정보 명시
    prompt = f"""
Role: You are Gemma, a super friendly staff at Gemma Burger.
Task: Summarize the customer's order based ONLY on the history below.

[Conversation]
{conversation_text}

[Rules]
1. If the customer hasn't confirmed any food orders yet, politely say: "It looks like you haven't finalized any orders yet! 🧐 Would you like to see the menu?"
2. Do NOT invent items. Only list what the CLERK explicitly confirmed.
3. Count the QUANTITY of each item carefully.
4. Use emojis (🧾, 🍔, 🥤) to make it look like a real receipt.
5. Output format example:
   "Here is your order so far! 🧾
   - [Quantity]x [Item Name] ($[Unit Price])
   - [Quantity]x [Item Name] ($[Unit Price])
   ----------------
   Total: $[Total Price]
   Is this correct? 😊"

Answer:"""
    
    return {"final_response": prompt}

def handle_general(state: AgentState):
    """일반 대화 및 문의 -> 전체 지식 검색"""
    query = state["messages"][-1]["content"]
    
    # 일반 문의는 메뉴일 수도 있고 매장 정보일 수도 있음 -> 필터 없이 전체 검색
    # (나중에 Router가 더 똑똑해지면 {"type": "info"}로 좁힐 수도 있음)
    docs = rag_engine.search(query) 
    context = "\n".join(docs)
    
    prompt = f"""
You are Gemma, a friendly staff at Gemma Burger.
Answer the customer's question based ONLY on the info below.

[Info]
{context}

Customer: {query}
Answer:"""
    return {"final_response": prompt}

def handle_order(state: AgentState):
    """주문 의도 -> 메뉴판(Menu)만 검색하여 검증"""
    query = state["messages"][-1]["content"]
    
    # 🟢 [핵심 수정] 주문 시에는 'type: menu' 데이터만 검색하도록 필터링!
    # 이렇게 하면 엉뚱한 매장 정보(주소, 와이파이 등)가 검색 결과에 섞이는 것을 방지합니다.
    print(f"🔍 [Agent] Verifying Order against Menu DB: '{query}'")
    
    # Pinecone 메타데이터 필터 문법 적용
    docs = rag_engine.search(query, filter={"type": "menu"})
    context = "\n".join(docs)
    
    prompt = f"""
You are Gemma, a smart waiter.
The customer wants to order: "{query}".

Check the [Menu Info] below.
1. Match the user's request to the OFFICIAL menu item name.
2. If found, accept the order and confirm the price.
3. If NOT found in the menu list, apologize and say we don't serve that.
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