from pydantic import BaseModel
from typing import Optional, Dict, List, Any


class FieldState(BaseModel):
    value: Optional[str] = None
    pending_value: Optional[str] = None
    status: str = "missing"
    confidence: str = "none"
    source: Optional[str] = None


class AssistantState(BaseModel):
    fields: Dict[str, FieldState]
    notes: List[str] = []
    pending_question: Optional[str] = "employment_status"


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    assistant_state: AssistantState
    suggested_fields: Dict[str, Optional[str]]
    progress: Dict[str, Any]

class ResetSessionRequest(BaseModel):
    session_id: str