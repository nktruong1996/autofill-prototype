from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models import ChatRequest, ChatResponse, ResetSessionRequest
from services.conversation import handle_chat, reset_session


app = FastAPI(title="FAS AI Autofill Demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {"status": "FAS AI Autofill service running"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    return handle_chat(request)

@app.post("/reset-session")
def reset(request: ResetSessionRequest):
    reset_session(request.session_id)
    return {
        "message": "Session reset successfully",
        "session_id": request.session_id,
    }