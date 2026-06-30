import json

from dynamic_fas.extraction import build_field_context
from dynamic_fas.models import DynamicAssistantState, DynamicFieldDefinition
from llm import DEPLOYMENT_NAME, client


SYSTEM_PROMPT = """
You are a helpful assistant for Financial Assistance Scheme form completion.
"""


def get_field_label(fields: list[DynamicFieldDefinition], field_id: str | None) -> str | None:
    for field in fields:
        if field.field_id == field_id:
            return field.label
    return None


def get_fallback_reply(
    state: DynamicAssistantState,
    fields: list[DynamicFieldDefinition],
) -> str:
    label = get_field_label(fields, state.pending_question)
    if label:
        return f"Thanks. Could you provide: {label}"

    return "Thanks. I have enough information for the required fields. You can review and apply the suggestions to the form."


def generate_assistant_reply(
    state: DynamicAssistantState,
    fields: list[DynamicFieldDefinition],
    user_message: str,
) -> str:
    prompt = f"""
You are helping a parent or guardian complete a dynamic Financial Assistance Scheme application form.

Available fields:
{build_field_context(fields)}

Current assistant state:
{json.dumps(state.model_dump(), indent=2)}

Latest user message:
{user_message}

Rules:
- Be concise and polite.
- Ask only one question at a time.
- Do not invent form values.
- Ask for the next missing required field based on pending_question.
- If all required fields are present, tell the user they can review and apply suggestions.
- Do not submit anything.
- Do not mention JSON, backend, APIs, or assistant_state.
"""

    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_completion_tokens=250,
        )
        content = response.choices[0].message.content
        if content and content.strip():
            return content.strip()
    except Exception as error:
        print("Dynamic conversation reply error:", repr(error))

    return get_fallback_reply(state, fields)
