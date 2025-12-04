from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.engine import engine
from app.rag import rag_engine  # ⬅️ RAG 엔진 추가

app = FastAPI(title="Gemma RAG Server")


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    """
    통합 채팅 엔드포인트: RAG 검색 -> 프롬프트 조립 -> 답변 생성
    """
    try:
        # 1. [RAG] 지식 검색
        retrieved_docs = rag_engine.search(req.message)
        context_str = "\n---\n".join(retrieved_docs)

        print(f"🔍 Context Found: {context_str}")  # 디버깅용 로그

        # 2. [Prompt] 시스템 프롬프트 조립
        system_prompt = f"""
You are Gemma, a friendly staff member at Gemma Burger.
Use the menu information below to answer the customer's question.
If the item is not in the menu, politely apologize.

[Menu Information]
{context_str}

Customer: {req.message}
Answer:
        """.strip()

        # 3. [Generate] 답변 생성
        response = engine.generate_text(
            prompt=system_prompt, max_tokens=300, temperature=0.7
        )

        return {"reply": response}

    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
