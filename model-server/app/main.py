from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.engine import engine
from app.agent import agent_app # ⬅️ 에이전트 앱 import

app = FastAPI(title="Gemma Agent Server")

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    try:
        print(f"📩 User Query: {req.message}")

        # 1. LangGraph 에이전트 실행
        # 에이전트가 의도를 파악하고 적절한 '프롬프트'를 결정해줍니다.
        initial_state = {
            "messages": [{"role": "user", "content": req.message}],
            "current_intent": "general",
            "order_items": [],
            "final_response": ""
        }
        
        # invoke()를 실행하면 그래프를 타고 끝까지 가서 결과를 줍니다.
        result = agent_app.invoke(initial_state)
        
        # 에이전트가 결정한 최종 프롬프트 가져오기
        final_prompt = result["final_response"]
        
        print(f"🤖 Agent decided prompt: {final_prompt[:50]}...")

        # 2. [Generate] 스트리밍 응답 생성 (기존 엔진 사용)
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