from dynamic_fas.change_detector import detect_changes
from dynamic_fas.conversation_llm import generate_assistant_reply
from dynamic_fas.extraction import (
    extract_information,
    is_negative_confirmation,
    is_positive_confirmation,
)
from dynamic_fas.form_help import generate_form_help_reply
from dynamic_fas.models import (
    DynamicAssistantState,
    DynamicChatRequest,
    DynamicChatResponse,
    DynamicFieldDefinition,
)
from dynamic_fas.state import (
    create_initial_state,
    get_field_map,
    get_progress,
    get_suggested_fields,
    reset_session,
    sessions,
    sync_state_fields,
)
from dynamic_fas.state_manager import (
    apply_changes,
    apply_pending_update,
    reject_pending_update,
)
from services.message_router import route_message


def build_response(
    session_id: str,
    state: DynamicAssistantState,
    fields: list[DynamicFieldDefinition],
    reply: str,
) -> DynamicChatResponse:
    sessions[session_id] = state
    return DynamicChatResponse(
        reply=reply,
        assistant_state=state,
        suggested_fields=get_suggested_fields(state),
        progress=get_progress(state, fields),
    )


def build_pending_update_reply(
    field_id: str,
    field_map: dict[str, DynamicFieldDefinition],
    state: DynamicAssistantState,
) -> str:
    field_definition = field_map.get(field_id)
    label = field_definition.label if field_definition else field_id.replace("_", " ")
    field_state = state.fields[field_id]

    return (
        f"You previously provided {label} as '{field_state.value}'. "
        f"Would you like to update it to '{field_state.pending_value}'?"
    )


def get_pending_update_id(state: DynamicAssistantState) -> str | None:
    if state.pending_update and state.pending_update in state.fields:
        return state.pending_update

    for field_id, field in state.fields.items():
        if field.status == "pending_update":
            return field_id

    return None


def handle_chat(request: DynamicChatRequest) -> DynamicChatResponse:
    fields = list(get_field_map(request.fields).values())
    state = sessions.get(request.session_id)

    if state is None:
        state = create_initial_state(fields)
    else:
        state = sync_state_fields(state, fields)

    field_map = get_field_map(fields)

    if state.pending_question != "confirm_update":
        route = route_message(request.message)

        if route.category == "FORM_HELP":
            reply = generate_form_help_reply(
                state=state,
                fields=fields,
                message=request.message,
            )
            return build_response(request.session_id, state, fields, reply)

        if route.category != "FORM_FILLING":
            return build_response(request.session_id, state, fields, route.reply)

    if state.pending_question == "confirm_update":
        if is_positive_confirmation(request.message):
            apply_pending_update(state, fields)

        elif is_negative_confirmation(request.message):
            reject_pending_update(state, fields)

        else:
            return build_response(
                request.session_id,
                state,
                fields,
                "Please confirm whether you would like me to update the existing information.",
            )

    else:
        extracted = extract_information(
            message=request.message,
            fields=fields,
            pending_question=state.pending_question,
        )
        changes = detect_changes(state, extracted)

        print("DYNAMIC EXTRACTED:", extracted)
        print("DYNAMIC CHANGES:", [change.model_dump() for change in changes])

        apply_changes(state, changes, fields)

    pending_update_id = get_pending_update_id(state)
    if pending_update_id:
        state.pending_question = "confirm_update"
        state.pending_update = pending_update_id
        return build_response(
            request.session_id,
            state,
            fields,
            build_pending_update_reply(pending_update_id, field_map, state),
        )

    reply = generate_assistant_reply(
        state=state,
        fields=fields,
        user_message=request.message,
    )

    return build_response(request.session_id, state, fields, reply)
