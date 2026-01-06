from app.agent.state import AgentState, Intent
from app.agent.utils import PROMPTS
from app.engine import engine


def classify_intent(state: AgentState):
    last_msg = state["messages"][-1]["content"]

    # YAML에서 라우터 프롬프트 가져오기
    prompt_template = PROMPTS["router"]["system"]
    prompt = prompt_template.format(user_message=last_msg)

    response = engine.generate_text(prompt, max_tokens=10, temperature=0.0)
    intent_raw = response.strip().upper()

    final_intent = Intent.GREETING.value
    for i in Intent:
        if i.name in intent_raw:
            final_intent = i.value
            break

    print(f"🧭 [Router] '{last_msg}' -> {intent_raw} -> {final_intent}")
    return {"current_intent": final_intent}
