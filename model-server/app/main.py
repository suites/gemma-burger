from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.engine import engine
from app.agent import agent_app

app = FastAPI(title="Gemma Agent Server")

class ChatRequest(BaseModel):
    message: str
    # 🟢 [추가] 세션 ID (없으면 서버에서 임시로 생성)
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
            # (나머지 필드는 그래프가 알아서 채우거나 유지합니다)
        }
        
        # 3. 에이전트 실행 (config 전달 필수!)
        result = agent_app.invoke(input_state, config=config)
        
        final_prompt = result["final_response"]
        
        # (디버깅용) 현재까지 쌓인 메시지 개수 확인
        history_count = len(result["messages"])
        print(f"🧠 Memory Depth: {history_count} messages")

        # 4. 스트리밍 응답
        return StreamingResponse(
            engine.generate_text_stream(
                prompt=final_prompt,
                max_tokens=500,
                temperature=0.7
            ),
            media_type="text/plain"
        )

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)