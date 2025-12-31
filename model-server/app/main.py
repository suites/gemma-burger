from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agent import agent_app, generate_customer_response
from app.engine import engine

app = FastAPI(title="Gemma Agent Server")


class ChatRequest(BaseModel):
    message: Optional[str] = None
    session_id: str = "default_guest"


@app.post("/chat/simulate")
async def run_simulation(req: ChatRequest):
    """Sara와 직원 간의 자율 대화 시뮬레이션을 실행합니다."""
    try:
        session_id = req.session_id
        config = {"configurable": {"thread_id": session_id}}

        async def simulation_generator():
            # 1. 시뮬레이션 초기화: Sara의 첫 인사
            current_input = generate_customer_response("sara", [])
            yield f"[SARA]: {current_input}\n\n"

            max_turns = 10  # 최대 10턴 제한
            for turn in range(max_turns):
                # 2. 직원의 응답 생성
                input_state = {
                    "messages": [{"role": "user", "content": current_input}],
                    "current_intent": "general",
                    "final_response": "",
                }

                # 에이전트 실행
                result = agent_app.invoke(input_state, config=config)
                final_prompt = result["final_response"]
                dynamic_temp = result.get("temperature", 0.7)

                # 직원의 답변 스트리밍 및 수집
                full_staff_response = ""
                yield "[ROSY]: "
                stream = engine.generate_text_stream(
                    prompt=final_prompt, max_tokens=300, temperature=dynamic_temp
                )
                for token in stream:
                    full_staff_response += token
                    yield token
                yield "\n\n"

                # 대화 기록 업데이트 (직원의 말 저장)
                agent_app.update_state(
                    config,
                    {
                        "messages": [
                            {"role": "assistant", "content": full_staff_response}
                        ]
                    },
                )

                # 3. 현재까지의 기록을 바탕으로 Sara의 다음 반응 생성
                # 현재 세션의 전체 메시지 가져오기
                current_state = agent_app.get_state(config)
                history = current_state.values.get("messages", [])

                current_input = generate_customer_response("sara", history)
                yield f"[SARA]: {current_input}\n\n"

                # 4. 종료 조건 확인
                if (
                    "[FINISH_ORDER]" in current_input
                    or "[CANCEL_ORDER]" in current_input
                ):
                    yield "--- Simulation Ended ---"
                    break

                # 대화 기록 업데이트 (손님의 말 저장)
                agent_app.update_state(
                    config, {"messages": [{"role": "user", "content": current_input}]}
                )

        return StreamingResponse(simulation_generator(), media_type="text/plain")

    except Exception as e:
        print(f"❌ Simulation Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Simulation failed")


@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    try:
        print(f"📩 User Query: {req.message} (Session: {req.session_id})")

        # 1. LangGraph 설정 (Thread ID 지정)
        # 이 ID가 같으면 이전 대화 기록(State)을 자동으로 불러옵니다.
        config = {"configurable": {"thread_id": req.session_id}}

        # 2. 입력 데이터 구성
        # operator.add 덕분에, 여기서 넣은 메시지는 기존 기록 뒤에 추가됩니다.
        input_state = {
            "messages": [{"role": "user", "content": req.message}],
            "current_intent": "general",
            "final_response": "",
        }

        # 3. 에이전트 실행 (config 전달 필수!)
        result = agent_app.invoke(input_state, config=config)
        final_prompt = result["final_response"]

        dynamic_temperature = result.get("temperature", 0.7)

        # (디버깅용) 현재까지 쌓인 메시지 개수 확인
        history_count = len(result["messages"])
        print(f"🧠 Memory Depth: {history_count} messages")

        async def response_generator():
            full_response = ""

            # 엔진에서 스트림을 받아서 클라이언트에게 전달
            stream = engine.generate_text_stream(
                prompt=final_prompt, max_tokens=500, temperature=dynamic_temperature
            )

            for token in stream:
                full_response += token
                yield token

            # 🟢 [핵심 수정] 스트리밍이 끝나면 완성된 답변을 메모리에 저장
            print(f"💾 Saving AI Response to Memory: {len(full_response)} chars")

            # update_state를 사용하여 assistant 메시지 추가
            # (이 코드는 스트리밍이 끝난 직후 서버 내부에서 실행됨)
            agent_app.update_state(
                config, {"messages": [{"role": "assistant", "content": full_response}]}
            )

        # 4. 스트리밍 응답
        return StreamingResponse(response_generator(), media_type="text/plain")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
