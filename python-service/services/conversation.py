from models import ChatRequest, ChatResponse
from assistant_state import (
    create_initial_state,
    get_suggested_fields,
    get_progress,
)
from services.extraction import (
    extract_information,
    is_positive_confirmation,
    is_negative_confirmation,
)
from services.change_detector import detect_changes
from services.state_manager import (
    apply_changes,
    apply_pending_update,
    reject_pending_update,
    update_pending_question,
)
from services.conversation_llm import generate_assistant_reply
from services.message_router import route_message
from services.form_help import generate_form_help_reply


sessions = {}

def reset_session(session_id: str) -> None:
    sessions.pop(session_id, None)

def build_response(session_id: str, state, reply: str) -> ChatResponse:
    sessions[session_id] = state

    return ChatResponse(
        reply=reply,
        assistant_state=state,
        suggested_fields=get_suggested_fields(state),
        progress=get_progress(state),
    )


def get_pending_update(state):
    return next(
        (
            (field_name, field)
            for field_name, field in state.fields.items()
            if field.status == "pending_update"
        ),
        None,
    )


def build_pending_update_reply(field_name: str, field) -> str:
    display_name = field_name.replace("_", " ")

    return (
        f"You previously provided {display_name} as "
        f"'{field.value}'. Would you like to update it to "
        f"'{field.pending_value}'?"
    )


def handle_chat(request: ChatRequest) -> ChatResponse:
    state = sessions.get(request.session_id)

    if state is None:
        state = create_initial_state()
    
    # Route non-form-filling messages before extraction.
    # Confirmation replies should still be handled by the confirmation flow.
    if state.pending_question != "confirm_update":
        route = route_message(request.message)

        if route.category == "FORM_HELP":
            reply = generate_form_help_reply(
                state=state,
                message=request.message,
            )

            return build_response(
                request.session_id,
                state,
                reply,
            )

        if route.category != "FORM_FILLING":
            return build_response(
                request.session_id,
                state,
                route.reply,
            )

    # 1. If we are waiting for confirmation, handle yes/no deterministically.
    if state.pending_question == "confirm_update":
        if is_positive_confirmation(request.message):
            apply_pending_update(state)
            update_pending_question(state)

        elif is_negative_confirmation(request.message):
            reject_pending_update(state)
            update_pending_question(state)

        else:
            return build_response(
                request.session_id,
                state,
                "Please confirm whether you would like me to update the existing information.",
            )

    # 2. Otherwise, extract information and detect changes.
    else:
        extracted = extract_information(
            message=request.message,
            pending_question=state.pending_question,
        )

        changes = detect_changes(state, extracted)

        print("EXTRACTED:", extracted.model_dump())
        print("CHANGES:", [change.model_dump() for change in changes])

        apply_changes(state, changes)

    # 3. If a field is pending update, force a deterministic confirmation reply.
    pending_update = get_pending_update(state)

    if pending_update:
        field_name, field = pending_update
        state.pending_question = "confirm_update"

        return build_response(
            request.session_id,
            state,
            build_pending_update_reply(field_name, field),
        )

    # 4. Otherwise, use GPT for normal conversational reply.
    reply = generate_assistant_reply(
        state=state,
        user_message=request.message,
    )

    return build_response(
        request.session_id,
        state,
        reply,
    )