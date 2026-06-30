from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


SupportedFieldType = Literal["text", "textarea", "select"]


class DynamicFieldDefinition(BaseModel):
    field_id: str
    label: str
    description: Optional[str] = None
    type: SupportedFieldType = "text"
    required: bool = False
    options: List[str] = Field(default_factory=list)

    @field_validator("field_id", "label")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value.strip()

    @field_validator("options")
    @classmethod
    def select_options_only(cls, value: List[str]) -> List[str]:
        return [option.strip() for option in value if option.strip()]


class DynamicFieldState(BaseModel):
    value: Optional[str] = None
    pending_value: Optional[str] = None
    status: str = "missing"
    confidence: str = "none"
    source: Optional[str] = None


class DynamicAssistantState(BaseModel):
    fields: Dict[str, DynamicFieldState]
    pending_question: Optional[str] = None
    pending_update: Optional[str] = None
    notes: List[str] = Field(default_factory=list)


class DynamicChatRequest(BaseModel):
    session_id: str
    message: str
    fields: List[DynamicFieldDefinition]


class DynamicChatResponse(BaseModel):
    reply: str
    assistant_state: DynamicAssistantState
    suggested_fields: Dict[str, Optional[str]]
    progress: Dict[str, Any]


class DynamicResetSessionRequest(BaseModel):
    session_id: str
