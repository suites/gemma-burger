from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.engine import engine
from app.rag import rag_engine

app = FastAPI(title="Gemma RAG Server")


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    try:
        print(f"📩 User Query: {req.message}")

        # 1. [RAG] 지식 검색
        retrieved_docs = rag_engine.search(req.message, k=3)
        context_str = "\n".join(retrieved_docs)

        if not context_str:
            context_str = "No specific menu information found."

        # 2. [Prompt] 프롬프트 조립
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

        # 3. [Generate] 스트리밍 응답 생성
        # engine의 제너레이터를 실행하여 StreamingResponse로 반환
        return StreamingResponse(
            engine.generate_text_stream(
                prompt=system_prompt, max_tokens=500, temperature=0.7
            ),
            media_type="text/plain",
        )

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
