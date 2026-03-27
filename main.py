import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from weather_agent_app import agent

app = FastAPI(title="Weather Intelligence Agent")

session_service = InMemorySessionService()
runner = Runner(
    agent=agent.root_agent,
    app_name="weather_intelligence_agent",
    session_service=session_service
)

@app.post("/ask")
async def ask_weather(request: Request):
    body = await request.json()
    question = body.get("question", "")

    if not question:
        return JSONResponse(
            status_code=400,
            content={"error": "question field is required"}
        )

    # Unique session per request
    session_id = f"session_{os.urandom(4).hex()}"

    await session_service.create_session(
        app_name="weather_intelligence_agent",
        user_id="user_1",
        session_id=session_id
    )

    message = Content(parts=[Part(text=question)])
    response_text = ""

    async for event in runner.run_async(
        user_id="user_1",
        session_id=session_id,
        new_message=message
    ):
        if event.is_final_response() and event.content:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text

    return JSONResponse(content={"answer": response_text})

@app.get("/health")
def health():
    return {"status": "ok", "agent": "weather_intelligence_agent"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
