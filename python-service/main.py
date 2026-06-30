from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dynamic_fas.conversation import (
    handle_chat as handle_dynamic_chat,
    reset_session as reset_dynamic_session,
)
from dynamic_fas.models import (
    DynamicChatRequest,
    DynamicChatResponse,
    DynamicResetSessionRequest,
)
from models import ChatRequest, ChatResponse, ResetSessionRequest
from services.conversation import handle_chat, reset_session


app = FastAPI(title="FAS AI Autofill Demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
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


@app.post("/dynamic-fas/chat", response_model=DynamicChatResponse)
def dynamic_chat(request: DynamicChatRequest):
    return handle_dynamic_chat(request)


@app.post("/dynamic-fas/reset-session")
def dynamic_reset(request: DynamicResetSessionRequest):
    reset_dynamic_session(request.session_id)
    return {
        "message": "Dynamic session reset successfully",
        "session_id": request.session_id,
    }
