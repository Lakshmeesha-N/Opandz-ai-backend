# src/agents/case_intake_agent/prompts/followup_question_prompt.py


def create_followup_question_prompt(
    missing_fields: list[str],
) -> str:
    """
    Generate a simple follow-up question
    for the missing fields.
    """

    return f"""
You are a legal intake assistant.

The following information is still missing:

{chr(10).join(f"- {field}" for field in missing_fields)}

Rules:

1. Ask ONE natural follow-up question.
2. Group related fields together.
3. Do not ask more than 3 important fields at once.
4. Be concise and professional.
5. Return only the question.

Example:

Could you please provide the accident date, place of accident, and petitioner's occupation?
"""