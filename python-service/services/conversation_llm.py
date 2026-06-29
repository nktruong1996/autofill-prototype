import json

from llm import client, DEPLOYMENT_NAME
from services.prompts import CONVERSATION_SYSTEM_PROMPT, CONVERSATION_USER_PROMPT
from models import AssistantState


def get_fallback_reply(state: AssistantState) -> str:
    if state.pending_question == "employment_status":
        return "Sure, I can help with that. Could you tell me your current employment status first?"

    if state.pending_question == "employer_name":
        return "Thanks. What is your employer name?"

    if state.pending_question == "application_reason":
        return "Thanks. Could you share the reason for your FAS application?"

    return "Thanks. I have enough information for the assisted fields. You can review the suggestions and apply them to the form."

def generate_assistant_reply(state: AssistantState, user_message: str) -> str:
    state_json = json.dumps(state.model_dump(), indent=2)

    prompt = CONVERSATION_USER_PROMPT.format(
    state_json=state_json,
    user_message=user_message,
)

    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {
                    "role": "system",
                    "content": CONVERSATION_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            max_completion_tokens=250,
        )

        content = response.choices[0].message.content

        if not content or not content.strip():
            return get_fallback_reply(state)

        return content.strip()

    except Exception as e:
        print("Conversation reply error:", repr(e))
        return "Thanks. Please review the suggested information and apply it to the form if it looks correct."