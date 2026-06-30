import json
from typing import Dict, Optional

from dynamic_fas.models import DynamicFieldDefinition
from llm import DEPLOYMENT_NAME, client


EXTRACTION_SYSTEM_PROMPT = """
You are a strict JSON extraction engine for a Financial Assistance Scheme form.
Return JSON only.
Do not include explanations.
"""


def build_field_context(fields: list[DynamicFieldDefinition]) -> str:
    lines = []
    for field in fields:
        option_text = ""
        if field.type == "select" and field.options:
            option_text = f"\n  options: {', '.join(field.options)}"

        lines.append(
            "\n".join(
                [
                    f"- field_id: {field.field_id}",
                    f"  label: {field.label}",
                    f"  description: {field.description or ''}",
                    f"  type: {field.type}",
                    f"  required: {field.required}",
                    option_text.rstrip(),
                ]
            ).strip()
        )

    return "\n\n".join(lines)


def build_empty_shape(fields: list[DynamicFieldDefinition]) -> Dict[str, Optional[str]]:
    return {field.field_id: None for field in fields}


def extract_information(
    message: str,
    fields: list[DynamicFieldDefinition],
    pending_question: Optional[str],
) -> Dict[str, str]:
    empty_shape = build_empty_shape(fields)
    prompt = f"""
Extract structured values from the user's latest message for the available fields.

Available fields:
{build_field_context(fields)}

Current pending question:
{pending_question}

Rules:
- Return JSON only.
- Use exactly the field_id values as JSON keys.
- Use null for fields not clearly provided.
- Extract only information explicitly provided by the user.
- Do not infer or invent missing values.
- A single message may provide multiple fields.
- If the user corrects a prior answer, extract only the corrected field value.
- The pending question is context only. Do not blindly use the message as that field's value.
- For select fields, return one of the provided options only when the user clearly indicates it.
- If a select answer is unclear or not one of the options, return null for that field.

User message:
{message}

Return JSON in this exact shape:
{json.dumps(empty_shape, indent=2)}
"""

    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_completion_tokens=1500,
        )
        content = response.choices[0].message.content
        data = json.loads(content)
    except Exception as error:
        print("Dynamic extraction error:", repr(error))
        data = {}

    allowed_ids = {field.field_id for field in fields}
    select_options = {
        field.field_id: field.options
        for field in fields
        if field.type == "select"
    }

    extracted: Dict[str, str] = {}
    for field_id, value in data.items():
        if field_id not in allowed_ids or value is None:
            continue

        normalized = str(value).strip()
        if not normalized:
            continue

        if field_id in select_options:
            matched = next(
                (
                    option
                    for option in select_options[field_id]
                    if option.lower() == normalized.lower()
                ),
                None,
            )
            if not matched:
                continue
            normalized = matched

        extracted[field_id] = normalized

    return extracted


def is_positive_confirmation(message: str) -> bool:
    normalized = message.lower().strip()
    return normalized in {
        "yes",
        "y",
        "yeah",
        "yep",
        "sure",
        "correct",
        "confirm",
        "ok",
        "okay",
        "please do",
        "update it",
    }


def is_negative_confirmation(message: str) -> bool:
    normalized = message.lower().strip()
    return normalized in {
        "no",
        "n",
        "nope",
        "incorrect",
        "cancel",
        "do not",
        "don't",
        "keep the old value",
        "reject",
    }
