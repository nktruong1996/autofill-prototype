import json
import re

from dynamic_fas.extraction import build_field_context
from dynamic_fas.models import DynamicAssistantState, DynamicFieldDefinition
from llm import DEPLOYMENT_NAME, client


SYSTEM_PROMPT = """
You help users understand how to complete a Financial Assistance Scheme form.
Keep answers short, practical, and focused on the supplied field metadata.
Do not answer eligibility, benefit amount, documents, deadlines, or policy questions.
"""


def normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def find_referenced_field(
    fields: list[DynamicFieldDefinition],
    message: str,
) -> DynamicFieldDefinition | None:
    normalized_message = f" {normalize_text(message)} "
    candidates: list[tuple[int, DynamicFieldDefinition, str]] = []

    for field in fields:
        field_candidates = {
            normalize_text(field.field_id),
            normalize_text(field.field_id.replace("_", " ")),
            normalize_text(field.label),
        }

        for candidate in field_candidates:
            if candidate:
                candidates.append((len(candidate), field, candidate))

    for _, field, candidate in sorted(candidates, key=lambda item: item[0], reverse=True):
        if f" {candidate} " in normalized_message:
            return field

    return None


def build_metadata_help_reply(field: DynamicFieldDefinition) -> str:
    description = field.description or "Provide the information requested by this field."
    required_text = "This field is required." if field.required else "This field is optional."

    if field.type == "select" and field.options:
        return (
            f"For {field.label}, choose the option that best matches the applicant's situation. "
            f"{description} {required_text} Available options are: {', '.join(field.options)}."
        )

    return (
        f"For {field.label}, enter a clear, brief answer. "
        f"{description} {required_text}"
    )


def generate_form_help_reply(
    state: DynamicAssistantState,
    fields: list[DynamicFieldDefinition],
    message: str,
) -> str:
    referenced_field = find_referenced_field(fields, message)
    if referenced_field:
        return build_metadata_help_reply(referenced_field)

    prompt = f"""
The user is asking for help with a dynamic FAS form.

Available fields:
{build_field_context(fields)}

Current assistant state:
{json.dumps(state.model_dump(), indent=2)}

User question:
{message}

Rules:
- Explain only how to fill the form.
- Use the field labels, descriptions, and select options when relevant.
- If the user asks what is still needed, mention missing required fields.
- If the user asks a policy question, say it should be handled by the FAQ assistant.
- Remind the user that suggestions are reviewable and not submitted automatically only when relevant.
- Do not mention APIs, JSON, backend, or internal state names.

Return a natural language reply only.
"""

    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_completion_tokens=400,
        )
        content = response.choices[0].message.content
        if content and content.strip():
            return content.strip()
    except Exception as error:
        print("Dynamic form help error:", repr(error))

    return "I can help explain what to enter for the fields in this form. Which field would you like help with?"
