from app.agent.state import AgentState
from app.agent.utils import PERSONAS, PROMPTS, build_prompt
from app.rag import rag_engine


def handle_order(state: AgentState):
    query = state["messages"][-1]["content"]
    docs = rag_engine.search(query, filter={"type": "menu"}, k=10)

    task = PROMPTS["order"]["task"]
    prompt = build_prompt("rosy", task, "\n".join(docs), query)

    return {"final_response": prompt, "temperature": 0.1}


def handle_history(state: AgentState):
    cart = state.get("cart", [])
    p = PERSONAS["rosy"]
    prefix = p["prefix"]

    if not cart:
        return {
            "final_response": f"{prefix}You haven't ordered anything yet! Feel free to ask about our menu!",
            "temperature": 0.0,
        }

    receipt_lines = []
    total_price = 0.0
    for item in cart:
        name = item.get("name", "Unknown Item")
        price = item.get("price", 0.0)
        qty = item.get("quantity", 1)
        receipt_lines.append(f"- {qty}x {name} (${price:.2f})")
        total_price += price * qty

    receipt_text = "\n".join(receipt_lines)
    final_response = f"""{prefix}Here is your order so far! 🧾
{receipt_text}
----------------
Total: ${total_price:.2f}
Is this correct?"""

    return {"final_response": final_response, "temperature": 0.0}


def handle_greeting(state: AgentState):
    user_msg = state["messages"][-1]["content"]
    if user_msg == "___INIT_GREETING___":
        user_msg = "Hello! I just walked in."

    return {
        "final_response": build_prompt("rosy", "Greet warmly. No info.", "", user_msg),
        "temperature": 0.7,
    }


# ... (handle_complaint, handle_menu_qa, handle_store_info 도 유사하게 작성)
# 공간상 생략했지만, 기존 로직에서 build_prompt와 PROMPTS[...]만 교체하면 됩니다.
# 나머지 함수들도 위 패턴대로 작성해 주세요.
def handle_complaint(state: AgentState):
    query = state["messages"][-1]["content"]
    print("🚨 [Agent] Complaint detected! Switching to Manager Gordon.")

    history = state["messages"]

    if len(history) < 4:
        task = "Listen to the customer's complaint and ask clarifying questions (e.g., dine-in/take-out, specific item) before offering any solutions."
        context = "Initial inquiry - focus on listening."
    else:
        docs = rag_engine.search(query, filter={"type": "info"}, k=5)
        context = "\n".join(docs)
        task = PROMPTS["complaint"]["task"]

    prompt = build_prompt("gordon", task, context, query)
    return {"final_response": prompt, "temperature": 0.2}


def handle_menu_qa(state):
    """메뉴 질문/추천 -> Rosy (메뉴판 검색)"""
    query = state["messages"][-1]["content"]

    docs = rag_engine.search(query, filter={"type": "menu"}, k=10)
    context = "\n".join(docs)

    task = PROMPTS["menu_qa"]["task"]

    prompt = build_prompt("rosy", task, context, query)

    return {"final_response": prompt, "temperature": 0.2}


def handle_store_info(state):
    """매장 시설 질문 -> Rosy (매장 정보 검색)"""
    query = state["messages"][-1]["content"]

    docs = rag_engine.search(query, filter={"type": "info"}, k=5)
    context = "\n".join(docs)

    task = PROMPTS["store_info"]["task"]

    prompt = build_prompt("rosy", task, context, query)

    # 정보 전달은 정확해야 하므로 온도를 낮춤
    return {"final_response": prompt, "temperature": 0.2}


def handle_cancel(state: AgentState):
    query = state["messages"][-1]["content"]
    task = PROMPTS["cancel"]["task"]
    prompt = build_prompt("rosy", task, "", query)

    return {
        "cart": [{"command": "RESET"}],
        "final_response": prompt,
        "temperature": 0.0,
    }


def handle_remove(state: AgentState):
    query = state["messages"][-1]["content"]
    task = PROMPTS["remove"]["task"]
    prompt = build_prompt("rosy", task, "", query)

    return {
        "final_response": prompt,
        "temperature": 0.0,
    }
