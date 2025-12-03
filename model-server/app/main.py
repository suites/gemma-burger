# model-server/app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.engine import engine

app = FastAPI(title="Gemma Inference Server")

# 1. 요청/응답 DTO 정의 (Pydantic)
class PromptRequest(BaseModel):
    prompt: str
    max_tokens: int = 200
    temperature: float = 0.7

class GenerationResponse(BaseModel):
    text: str

@app.get("/health")
def health_check():
    return {"status": "ok", "device": "Apple Silicon (Metal)"}

@app.post("/generate", response_model=GenerationResponse)
def generate(req: PromptRequest):
    """
    LLM 추론 엔드포인트
    NestJS로부터 완성된 프롬프트를 받아 텍스트를 생성합니다.
    """
    try:
        generated_text = engine.generate_text(
            prompt=req.prompt,
            max_tokens=req.max_tokens,
            temp=req.temperature
        )
        return GenerationResponse(text=generated_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # 개발용 실행 설정
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)