import json

from llm import client, DEPLOYMENT_NAME
from models import AssistantState
from services.prompts import (
    FORM_HELP_SYSTEM_PROMPT,
    FORM_HELP_USER_PROMPT,
)


def generate_form_help_reply(state: AssistantState, message: str) -> str:
    state_json = json.dumps(state.model_dump(), indent=2)

    prompt = FORM_HELP_USER_PROMPT.format(
        state_json=state_json,
        message=message,
    )

    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {
                    "role": "system",
                    "content": FORM_HELP_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            max_completion_tokens=400,
        )

        content = response.choices[0].message.content

        if not content or not content.strip():
            return "I can help explain how to complete the FAS form fields. What would you like help with?"

        return content.strip()

    except Exception as e:
        print("Form help error:", repr(e))
        return "I can help explain how to complete the FAS form fields. What would you like help with?"