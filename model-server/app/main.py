from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.engine import engine
from app.agent import agent_app

app = FastAPI(title="Gemma Agent Server")

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_guest"

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
            "final_response": ""
        }
        
        # 3. 에이전트 실행 (config 전달 필수!)
        result = agent_app.invoke(input_state, config=config)
        
        final_prompt = result["final_response"]
        
        # (디버깅용) 현재까지 쌓인 메시지 개수 확인
        history_count = len(result["messages"])
        print(f"🧠 Memory Depth: {history_count} messages")

        async def response_generator():
            full_response = ""
            
            # 엔진에서 스트림을 받아서 클라이언트에게 전달
            stream = engine.generate_text_stream(
                prompt=final_prompt,
                max_tokens=500,
                temperature=0.7
            )
            
            for token in stream:
                full_response += token
                yield token
            
            # 🟢 [핵심 수정] 스트리밍이 끝나면 완성된 답변을 메모리에 저장
            print(f"💾 Saving AI Response to Memory: {len(full_response)} chars")
            
            # update_state를 사용하여 assistant 메시지 추가
            # (이 코드는 스트리밍이 끝난 직후 서버 내부에서 실행됨)
            agent_app.update_state(
                config,
                {"messages": [{"role": "assistant", "content": full_response}]}
            )


        # 4. 스트리밍 응답
        return StreamingResponse(
            response_generator(),
            media_type="text/plain"
        )

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)