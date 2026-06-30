MESSAGE_ROUTER_SYSTEM_PROMPT = """
You classify the latest message sent to an assistant that helps a user answer
open questions in a Financial Assistance Scheme application.
Return JSON only and never add explanations.
"""


MESSAGE_ROUTER_USER_PROMPT = """
Classify the message into exactly one category:

- FORM_FILLING: the user provides personal circumstances or an answer that may
  be used for one of the application questions.
- FORM_HELP: the user asks what a question means or how to answer the form.
- FAQ_REDIRECT: the user asks about eligibility, benefits, required documents,
  deadlines, official policy, or application rules.
- OFF_TOPIC: the message is unrelated to completing the FAS form.

If the message might contain an answer for the form, choose FORM_FILLING.

Message:
{message}

Return exactly:
{{"category": "FORM_FILLING"}}
"""


EXTRACTION_SYSTEM_PROMPT = """
You are a strict information extraction engine for open questions in a
Financial Assistance Scheme form. Return JSON only. Never invent, assume, or
complete missing facts for the user.
"""


EXTRACTION_USER_PROMPT = """
Extract answers from the user's latest message for the configured questions.

Configured questions:
{questions_json}

Current question being asked, if any:
{pending_question_id}

User message:
{message}

Rules:
- Extract only information clearly stated by the user.
- A message can answer zero, one, or multiple questions.
- Use only question_id values from the configured questions.
- Do not copy one statement into unrelated questions.
- Do not answer questions on the user's behalf.
- The current question is context only; do not blindly treat every message as
  its answer.
- Keep the answer concise while preserving the user's meaning.
- If nothing is clearly provided, return an empty answers object.

Return exactly this JSON shape:
{{
  "answers": {{
    "101": "Clearly provided answer"
  }}
}}
"""
