import json
from typing import Literal

from pydantic import BaseModel

from dynamic_fas.prompts import (
    MESSAGE_ROUTER_SYSTEM_PROMPT,
    MESSAGE_ROUTER_USER_PROMPT,
)


RouteCategory = Literal["FORM_FILLING", "FORM_HELP", "FAQ_REDIRECT", "OFF_TOPIC"]


class MessageRoute(BaseModel):
    category: RouteCategory
    reply: str | None = None


def _route_reply(category: RouteCategory) -> str | None:
    if category == "FAQ_REDIRECT":
        return (
            "This question concerns FAS policy or eligibility. Please refer to "
            "the official information or contact the FAS support team."
        )
    if category == "OFF_TOPIC":
        return "I can only help you complete the questions in the FAS application."
    return None


def _rule_route(message: str) -> MessageRoute | None:
    normalized = message.lower().strip()

    form_help_patterns = [
        "điền gì",
        "trả lời thế nào",
        "trả lời sao",
        "câu này nghĩa là gì",
        "câu hỏi này",
        "how should i answer",
        "what should i write",
        "what does this mean",
    ]
    faq_patterns = [
        "đủ điều kiện",
        "được bao nhiêu tiền",
        "cần giấy tờ",
        "hạn chót",
        "hạn nộp",
        "income criteria",
        "eligible",
        "deadline",
        "documents required",
    ]
    off_topic_patterns = [
        "thời tiết",
        "kể chuyện cười",
        "viết code",
        "gợi ý phim",
        "weather",
        "tell me a joke",
        "recommend a movie",
    ]

    if any(pattern in normalized for pattern in faq_patterns):
        return MessageRoute(
            category="FAQ_REDIRECT",
            reply=_route_reply("FAQ_REDIRECT"),
        )

    if any(pattern in normalized for pattern in off_topic_patterns):
        return MessageRoute(
            category="OFF_TOPIC",
            reply=_route_reply("OFF_TOPIC"),
        )

    if any(pattern in normalized for pattern in form_help_patterns):
        return MessageRoute(category="FORM_HELP")

    return None


def route_message(message: str) -> MessageRoute:
    rule_route = _rule_route(message)
    if rule_route is not None:
        return rule_route

    try:
        # Imported lazily so unit tests and non-AI routes do not require Azure
        # credentials during module import.
        from llm import DEPLOYMENT_NAME, client

        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": MESSAGE_ROUTER_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": MESSAGE_ROUTER_USER_PROMPT.format(message=message),
                },
            ],
            max_completion_tokens=200,
        )
        content = response.choices[0].message.content or ""
        data = json.loads(content)
        category = data.get("category")

        if category in {"FORM_FILLING", "FORM_HELP", "FAQ_REDIRECT", "OFF_TOPIC"}:
            return MessageRoute(category=category, reply=_route_reply(category))
    except Exception as error:
        print("Dynamic FAS routing error:", repr(error))

    # Information-bearing messages are the safe fallback: extraction still has
    # a strict allow-list of configured question IDs.
    return MessageRoute(category="FORM_FILLING")
