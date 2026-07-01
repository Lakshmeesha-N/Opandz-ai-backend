# src/agents/case_intake_agent/prompts/followup_question_prompt.py


def create_followup_question_prompt(
    missing_fields: list[str],
    user_message: str = "",
) -> str:
    """
    Generate a conversational follow-up question
    for the missing fields, acknowledging the user's last message.
    """

    user_context = (
        f"The user just said: \"{user_message}\"\n\n"
        if user_message and user_message.strip()
        else ""
    )

    return f"""
You are a friendly legal intake assistant.

{user_context}The following information is still missing from the case:

{chr(10).join(f"- {field}" for field in missing_fields)}

Rules:

1. If the user sent a greeting or a general message (e.g. "hi", "hello"), briefly acknowledge it in one sentence.
2. Then ask ONE natural follow-up question to collect the next missing field(s).
3. Group related fields together if needed.
4. Do not ask more than 3 fields at once.
5. Be concise and professional.
6. Return only the response (acknowledgement + question).

Example:

Hi! Happy to help. Could you please provide the accident date, place of accident, and petitioner's occupation?
"""