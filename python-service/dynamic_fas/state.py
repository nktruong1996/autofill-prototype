from typing import Dict, List

from dynamic_fas.models import (
    DynamicAssistantState,
    DynamicFieldDefinition,
    DynamicFieldState,
)


sessions: Dict[str, DynamicAssistantState] = {}


def supported_fields(fields: List[DynamicFieldDefinition]) -> List[DynamicFieldDefinition]:
    return [field for field in fields if field.type in {"text", "textarea", "select"}]


def get_field_map(fields: List[DynamicFieldDefinition]) -> Dict[str, DynamicFieldDefinition]:
    return {field.field_id: field for field in supported_fields(fields)}


def create_initial_state(fields: List[DynamicFieldDefinition]) -> DynamicAssistantState:
    field_map = get_field_map(fields)
    state = DynamicAssistantState(
        fields={
            field_id: DynamicFieldState()
            for field_id in field_map.keys()
        },
        notes=[],
    )
    update_pending_question(state, fields)
    return state


def sync_state_fields(
    state: DynamicAssistantState,
    fields: List[DynamicFieldDefinition],
) -> DynamicAssistantState:
    field_map = get_field_map(fields)

    for field_id in field_map.keys():
        if field_id not in state.fields:
            state.fields[field_id] = DynamicFieldState()

    for field_id in list(state.fields.keys()):
        if field_id not in field_map:
            del state.fields[field_id]

    if state.pending_update and state.pending_update not in state.fields:
        state.pending_update = None

    if state.pending_question and state.pending_question not in state.fields:
        state.pending_question = None

    update_pending_question(state, fields)
    return state


def reset_session(session_id: str) -> None:
    sessions.pop(session_id, None)


def get_required_field_ids(fields: List[DynamicFieldDefinition]) -> List[str]:
    return [field.field_id for field in supported_fields(fields) if field.required]


def get_suggested_fields(state: DynamicAssistantState) -> dict:
    return {
        field_id: field.value
        for field_id, field in state.fields.items()
        if field.status in {"suggested", "confirmed"} and field.value is not None
    }


def get_progress(
    state: DynamicAssistantState,
    fields: List[DynamicFieldDefinition],
) -> dict:
    required_fields = get_required_field_ids(fields)
    completed = sum(
        1
        for field_id in required_fields
        if field_id in state.fields
        and state.fields[field_id].status in {"suggested", "confirmed"}
    )

    return {
        "completed": completed,
        "total": len(required_fields),
        "completed_required_fields": completed,
        "total_required_fields": len(required_fields),
        "required_fields": required_fields,
    }


def has_pending_update(state: DynamicAssistantState) -> bool:
    return any(field.status == "pending_update" for field in state.fields.values())


def update_pending_question(
    state: DynamicAssistantState,
    fields: List[DynamicFieldDefinition],
) -> None:
    if has_pending_update(state):
        state.pending_question = "confirm_update"
        return

    for field_id in get_required_field_ids(fields):
        field = state.fields.get(field_id)
        if field and field.status == "missing":
            state.pending_question = field_id
            return

    state.pending_question = None
