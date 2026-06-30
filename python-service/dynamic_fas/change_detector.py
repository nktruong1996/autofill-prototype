from typing import Dict, List, Optional

from pydantic import BaseModel

from dynamic_fas.models import DynamicAssistantState


class DynamicFieldChange(BaseModel):
    field_id: str
    old_value: Optional[str] = None
    new_value: str
    change_type: str


def normalize_value(value: str) -> str:
    return " ".join(value.strip().split())


def detect_changes(
    state: DynamicAssistantState,
    extracted: Dict[str, str],
) -> List[DynamicFieldChange]:
    changes: List[DynamicFieldChange] = []

    for field_id, raw_value in extracted.items():
        if field_id not in state.fields or raw_value is None:
            continue

        new_value = normalize_value(str(raw_value))
        if not new_value:
            continue

        old_value = state.fields[field_id].value

        if not old_value:
            changes.append(
                DynamicFieldChange(
                    field_id=field_id,
                    old_value=None,
                    new_value=new_value,
                    change_type="new",
                )
            )
        elif normalize_value(old_value).lower() == new_value.lower():
            changes.append(
                DynamicFieldChange(
                    field_id=field_id,
                    old_value=old_value,
                    new_value=new_value,
                    change_type="same",
                )
            )
        else:
            changes.append(
                DynamicFieldChange(
                    field_id=field_id,
                    old_value=old_value,
                    new_value=new_value,
                    change_type="update",
                )
            )

    return changes
