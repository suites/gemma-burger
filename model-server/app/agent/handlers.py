from app.agent.state import AgentState
from app.agent.utils import PERSONAS, PROMPTS, build_prompt
from app.rag import rag_engine


def handle_order(state: AgentState):
    query = state["messages"][-1]["content"]
    docs = rag_engine.search(query, filter={"type": "menu"})

    # YAML에서 Task 지시문 가져오기
    task = PROMPTS["order"]["task"]

    prompt = build_prompt("rosy", task, "\n".join(docs), query)
    return {"final_response": prompt, "temperature": 0.7}


def handle_history(state: AgentState):
    # 대화 기록 포맷팅
    history_lines = [f"{m['role'].upper()}: {m['content']}" for m in state["messages"]]
    conversation_text = "\n".join(history_lines)

    p = PERSONAS["rosy"]
    config = PROMPTS["history"]  # YAML 설정

    # 프롬프트 조립 (YAML 내 변수 치환)
    system_prompt = f"""
    You are {p["name"]}, {p["description"]}.
    Task: {config["task"]}
    
    [Conversation]
    {conversation_text}
    
    [Rules]
    {config["rules"].format(prefix=p["prefix"])}
    
    Answer:"""

    return {"final_response": system_prompt, "temperature": 0.0}


def handle_greeting(state: AgentState):
    return {
        "final_response": build_prompt(
            "rosy", "Greet warmly. No info.", "", state["messages"][-1]["content"]
        ),
        "temperature": 0.7,
    }


# ... (handle_complaint, handle_menu_qa, handle_store_info 도 유사하게 작성)
# 공간상 생략했지만, 기존 로직에서 build_prompt와 PROMPTS[...]만 교체하면 됩니다.
# 나머지 함수들도 위 패턴대로 작성해 주세요.
def handle_complaint(state):
    """불만 접수 -> Gordon (규정 검색)"""
    query = state["messages"][-1]["content"]
    print("🚨 [Agent] Complaint detected! Switching to Manager Gordon.")

    # 규정(Policy/Info) 정보 검색
    docs = rag_engine.search(query, filter={"type": "info"})
    context = "\n".join(docs)

    # Gordon에게 맞는 Task 로드
    task = PROMPTS["complaint"]["task"]

    prompt = build_prompt("gordon", task, context, query)
    return {"final_response": prompt, "temperature": 0.2}


def handle_menu_qa(state):
    """메뉴 질문/추천 -> Rosy (메뉴판 검색)"""
    query = state["messages"][-1]["content"]

    # 메뉴 정보만 검색
    docs = rag_engine.search(query, filter={"type": "menu"})
    context = "\n".join(docs)

    task = PROMPTS["menu_qa"]["task"]

    prompt = build_prompt("rosy", task, context, query)
    return {"final_response": prompt, "temperature": 0.5}


def handle_store_info(state):
    """매장 시설 질문 -> Rosy (매장 정보 검색)"""
    query = state["messages"][-1]["content"]

    # 매장 정보(WiFi, 시간 등)만 검색
    docs = rag_engine.search(query, filter={"type": "info"})
    context = "\n".join(docs)

    task = PROMPTS["store_info"]["task"]

    prompt = build_prompt("rosy", task, context, query)

    # 정보 전달은 정확해야 하므로 온도를 낮춤
    return {"final_response": prompt, "temperature": 0.2}
