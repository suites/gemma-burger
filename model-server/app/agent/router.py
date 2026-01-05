from app.agent.state import AgentState
from app.agent.utils import PROMPTS
from app.engine import engine


def classify_intent(state: AgentState):
    last_msg = state["messages"][-1]["content"]

    # YAML에서 라우터 프롬프트 가져오기
    prompt_template = PROMPTS["router"]["system"]
    prompt = prompt_template.format(user_message=last_msg)

    response = engine.generate_text(prompt, max_tokens=10, temperature=0.0)
    intent = response.strip().upper()

    # 간단한 매핑
    valid_intents = [
        "ORDER",
        "HISTORY",
        "COMPLAINT",
        "GREETING",
        "MENU_QA",
        "STORE_INFO",
    ]

    # 포함 여부 확인 (예: "ORDER NOW" -> "ORDER")
    final_intent = "greeting"  # Default
    for v in valid_intents:
        if v in intent:
            final_intent = v.lower()
            break

    print(f"🧭 [Router] '{last_msg}' -> {intent} -> {final_intent}")
    return {"current_intent": final_intent}
