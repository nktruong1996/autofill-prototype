from dynamic_fas.change_detector import DynamicFieldChange
from dynamic_fas.models import DynamicAssistantState, DynamicFieldDefinition
from dynamic_fas.state import update_pending_question


def get_first_pending_update_id(state: DynamicAssistantState) -> str | None:
    for field_id, field in state.fields.items():
        if field.status == "pending_update":
            return field_id

    return None


def apply_changes(
    state: DynamicAssistantState,
    changes: list[DynamicFieldChange],
    fields: list[DynamicFieldDefinition],
) -> None:
    for change in changes:
        field = state.fields[change.field_id]

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
            if state.pending_update is None:
                state.pending_update = change.field_id

    if state.pending_update is None:
        state.pending_update = get_first_pending_update_id(state)
    update_pending_question(state, fields)


def apply_pending_update(
    state: DynamicAssistantState,
    fields: list[DynamicFieldDefinition],
) -> bool:
    field_id = state.pending_update or get_first_pending_update_id(state)
    field = state.fields.get(field_id) if field_id else None

    if field and field.status == "pending_update" and field.pending_value:
        field.value = field.pending_value
        field.pending_value = None
        field.status = "suggested"
        state.pending_update = get_first_pending_update_id(state)
        update_pending_question(state, fields)
        return True

    state.pending_update = None
    update_pending_question(state, fields)
    return False


def reject_pending_update(
    state: DynamicAssistantState,
    fields: list[DynamicFieldDefinition],
) -> bool:
    field_id = state.pending_update or get_first_pending_update_id(state)
    field = state.fields.get(field_id) if field_id else None

    if field and field.status == "pending_update":
        field.pending_value = None
        field.status = "suggested" if field.value else "missing"
        state.pending_update = get_first_pending_update_id(state)
        update_pending_question(state, fields)
        return True

    state.pending_update = None
    update_pending_question(state, fields)
    return False
