import json
from typing import Optional
from pydantic import BaseModel

from llm import client, DEPLOYMENT_NAME
from services.prompts import (
    MESSAGE_ROUTER_SYSTEM_PROMPT,
    MESSAGE_ROUTER_USER_PROMPT,
)


class MessageRoute(BaseModel):
    category: str
    reply: Optional[str] = None


VALID_CATEGORIES = {
    "FORM_FILLING",
    "FORM_HELP",
    "FAQ_REDIRECT",
    "OFF_TOPIC",
}


def build_router_reply(category: str) -> str:
    if category == "FORM_HELP":
        return (
            "I can help collect information for the FAS form, such as your "
            "employment status, employer name, and application reason. "
            "You can review any suggestions before applying them to the form."
        )

    if category == "FAQ_REDIRECT":
        return (
            "That question is better handled by the FAQ assistant. "
            "I can help collect information for this FAS form."
        )

    if category == "OFF_TOPIC":
        return (
            "I can only help with completing the FAS form. "
            "Please ask me about the form or provide information for the application."
        )

    return ""


def route_message(message: str) -> MessageRoute:
    rule_route = route_by_rules(message)

    if rule_route is not None:
        return rule_route
    
    prompt = MESSAGE_ROUTER_USER_PROMPT.format(message=message)

    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {
                    "role": "system",
                    "content": MESSAGE_ROUTER_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            max_completion_tokens=300,
        )

        content = response.choices[0].message.content

        if not content or not content.strip():
            return MessageRoute(category="FORM_FILLING")

        data = json.loads(content)
        category = data.get("category", "FORM_FILLING")

        if category not in VALID_CATEGORIES:
            category = "FORM_FILLING"

        reply = build_router_reply(category)

        return MessageRoute(
            category=category,
            reply=reply,
        )

    except Exception as e:
        print("Message routing error:", repr(e))
        return MessageRoute(category="FORM_FILLING")

def route_by_rules(message: str) -> MessageRoute | None:
    normalized = message.lower().strip()

    form_help_patterns = [
        "what type of information",
        "what information",
        "what should i put",
        "what should i write",
        "what do i put",
        "how do i fill",
        "how should i fill",
        "what does",
        "why do you need",
        "can i edit",
        "how does this autofill work",
    ]

    if any(pattern in normalized for pattern in form_help_patterns):
        return MessageRoute(
            category="FORM_HELP",
            reply=build_router_reply("FORM_HELP"),
        )

    return None