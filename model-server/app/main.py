import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agent import agent_app
from app.agent.state import Intent
from app.engine import engine


def validate_required_environment_variables():
    required_vars = ["PINECONE_API_KEY", "PINECONE_INDEX_NAME"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing_vars)}. "
            f"Please check your .env file."
        )


validate_required_environment_variables()

app = FastAPI(title="Gemma Agent Server")


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_guest"


@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    try:
        print(f"📩 User Query: {req.message} (Session: {req.session_id})")

        config = {"configurable": {"thread_id": req.session_id}}

        input_state = {
            "messages": [{"role": "user", "content": req.message}],
            "current_intent": Intent.GREETING.value,
            "final_response": "",
        }

        result = agent_app.invoke(input_state, config=config)
        final_prompt = result["final_response"]

        dynamic_temperature = result.get("temperature", 0.7)

        history_count = len(result["messages"])
        print(f"🧠 Memory Depth: {history_count} messages")

        async def response_generator():
            full_response = ""

            try:
                stream = engine.generate_text_stream(
                    prompt=final_prompt,
                    max_tokens=500,
                    temperature=dynamic_temperature,
                )

                for token in stream:
                    full_response += token
                    yield token

                print(f"💾 Saving AI Response to Memory: {len(full_response)} chars")

                agent_app.update_state(
                    config,
                    {"messages": [{"role": "assistant", "content": full_response}]},
                )

            except Exception as stream_error:
                error_msg = f"Error during text generation: {str(stream_error)}"
                print(f"❌ {error_msg}")
                yield f"\n\n[Error: {error_msg}]"

        return StreamingResponse(response_generator(), media_type="text/plain")

    except KeyError as e:
        print(f"❌ Missing key in agent state: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Agent configuration error: {str(e)}"
        )
    except RuntimeError as e:
        print(f"❌ Runtime error: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Model service error: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
