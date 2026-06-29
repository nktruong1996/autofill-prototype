from models import AssistantState


def build_reply(state: AssistantState) -> str:
    if any(field.status == "conflict" for field in state.fields.values()):
        return "I noticed that some information conflicts with what was provided earlier. Could you confirm the correct details?"

    if state.pending_question == "employment_status":
        return "I can help collect your employment status, employer name, and application reason for the FAS form. Could you tell me your current employment status?"

    if state.pending_question == "employer_name":
        return "Thanks. I noted your employment status. What is your employer name?"

    if state.pending_question == "application_reason":
        return "Thanks. Could you share the reason for your FAS application?"

    return "Thanks. I have enough information for the assisted fields. You can review the suggestions and apply them to the form."