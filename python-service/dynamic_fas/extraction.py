import json

from dynamic_fas.models import DynamicQuestion
from dynamic_fas.prompts import EXTRACTION_SYSTEM_PROMPT, EXTRACTION_USER_PROMPT


def _parse_json(content: str) -> dict:
    normalized = content.strip()
    if normalized.startswith("```"):
        normalized = normalized.removeprefix("```json").removeprefix("```")
        normalized = normalized.removesuffix("```").strip()
    return json.loads(normalized)


def extract_answers(
    message: str,
    questions: list[DynamicQuestion],
    pending_question_id: int | None,
) -> dict[str, str]:
    question_payload = [
        {
            "question_id": question.question_id,
            "question_text": question.question_text,
            "is_required": question.is_required,
        }
        for question in questions
    ]
    prompt = EXTRACTION_USER_PROMPT.format(
        questions_json=json.dumps(question_payload, ensure_ascii=False, indent=2),
        pending_question_id=pending_question_id,
        message=message,
    )

    try:
        from llm import DEPLOYMENT_NAME, client

        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_completion_tokens=1200,
        )
        content = response.choices[0].message.content or ""
        data = _parse_json(content)
        raw_answers = data.get("answers", {})
    except Exception as error:
        print("Dynamic FAS extraction error:", repr(error))
        return {}

    allowed_ids = {str(question.question_id) for question in questions}
    answers: dict[str, str] = {}

    if not isinstance(raw_answers, dict):
        return answers

    for question_id, value in raw_answers.items():
        key = str(question_id)
        if key not in allowed_ids or not isinstance(value, str):
            continue

        normalized_value = value.strip()
        if normalized_value:
            answers[key] = normalized_value[:4000]

    return answers


def is_positive_confirmation(message: str) -> bool:
    return message.lower().strip() in {
        "có",
        "đồng ý",
        "xác nhận",
        "cập nhật",
        "yes",
        "y",
        "yeah",
        "ok",
        "okay",
        "confirm",
    }


def is_negative_confirmation(message: str) -> bool:
    return message.lower().strip() in {
        "không",
        "không đồng ý",
        "giữ câu cũ",
        "giữ nguyên",
        "từ chối",
        "no",
        "n",
        "cancel",
        "reject",
    }
