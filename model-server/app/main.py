# model-server/app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.engine import engine
from app.rag import rag_engine

app = FastAPI(title="Gemma RAG Server")


# 요청 데이터 모델 (NestJS가 보낼 데이터)
class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    """
    RAG 파이프라인: Retrieval(검색) -> Augmented(프롬프트 조립) -> Generation(생성)
    """
    try:
        print(f"📩 User Query: {req.message}")

        # 1. [Retrieval] 지식 검색 (Pinecone)
        # 질문과 관련된 메뉴 3개를 가져옵니다.
        retrieved_docs = rag_engine.search(req.message, k=3)
        context_str = "\n".join(retrieved_docs)

        # 검색된 내용이 없으면(빈 리스트) 처리
        if not context_str:
            context_str = "No specific menu information found."

        print(f"🔍 Context Found:\n{context_str}")

        # 2. [Augmented] 프롬프트 엔지니어링
        # 시스템 페르소나 + 검색된 지식 + 사용자 질문 결합
        system_prompt = f"""
You are Gemma, a friendly staff member at Gemma Burger.
Answer the customer's question based ONLY on the menu information below.
If the item is not in the menu, politely apologize.
Use emojis to make the conversation lively.

[Menu Information]
{context_str}

Customer: {req.message}
Answer:
        """.strip()

        # 3. [Generation] 답변 생성
        response = engine.generate_text(
            prompt=system_prompt, max_tokens=300, temperature=0.7
        )

        return {"reply": response}

    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    # 개발용 실행
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
