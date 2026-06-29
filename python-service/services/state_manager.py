from models import AssistantState
from services.extraction import ExtractedInfo
from assistant_state import get_required_fields
from services.change_detector import FieldChange


def update_field(state: AssistantState, field_name: str, value: str, confidence: str = "medium") -> None:
    field = state.fields[field_name]

    if field.value and field.value != value:
        field.pending_value = value
        field.status = "pending_update"
        field.confidence = confidence
        field.source = "user_message"
        return

    field.value = value
    field.pending_value = None
    field.status = "suggested"
    field.confidence = confidence
    field.source = "user_message"

def has_pending_update(state: AssistantState) -> bool:
    return any(
        field.status == "pending_update"
        for field in state.fields.values()
    )


def apply_pending_update(state: AssistantState) -> bool:
    for field in state.fields.values():
        if field.status == "pending_update" and field.pending_value:
            field.value = field.pending_value
            field.pending_value = None
            field.status = "suggested"
            return True

    return False


def reject_pending_update(state: AssistantState) -> bool:
    for field in state.fields.values():
        if field.status == "pending_update":
            field.pending_value = None
            field.status = "suggested"
            return True

    return False


def update_state_from_extraction(state: AssistantState, extracted: ExtractedInfo) -> None:
    if extracted.employment_status:
        update_field(
            state,
            "employment_status",
            extracted.employment_status,
            confidence="high",
        )

    if extracted.employer_name:
        update_field(
            state,
            "employer_name",
            extracted.employer_name,
            confidence="medium",
        )

    if extracted.application_reason:
        update_field(
            state,
            "application_reason",
            extracted.application_reason,
            confidence="medium",
        )

    update_pending_question(state)


def update_pending_question(state: AssistantState) -> None:
    if has_pending_update(state):
        state.pending_question = "confirm_update"
        return

    required_fields = get_required_fields(state)

    for field_name in required_fields:
        if state.fields[field_name].status == "missing":
            state.pending_question = field_name
            return

    state.pending_question = None

def apply_changes(state: AssistantState, changes: list[FieldChange]) -> None:
    for change in changes:
        field = state.fields[change.field_name]

        if change.change_type == "new":
            field.value = change.new_value
            field.pending_value = None
            field.status = "suggested"
            field.confidence = "medium"
            field.source = "user_message"

        elif change.change_type == "same":
            continue

        elif change.change_type == "update":
            field.pending_value = change.new_value
            field.status = "pending_update"
            field.confidence = "medium"
            field.source = "user_message"

    update_pending_question(state)