# src/agents/case_intake_agent/nodes/generate_followup_question.py

from src.agents.case_intake_agent.schema.global_state import (
    AgentState,
)

from src.agents.case_intake_agent.prompts.followup_question_prompt import (
    create_followup_question_prompt,
)

from src.llm.llm import get_llm


async def generate_followup_question(
    state: AgentState,
) -> AgentState:
    """
    Generate a single follow-up question
    from the missing fields.
    """

    try:

        missing_fields = state.get(
            "missing_fields",
            [],
        )

        if not missing_fields:

            return {
                **state,
                "next_question": None,
                "error": None,
            }

        prompt = create_followup_question_prompt(
            missing_fields=missing_fields,
        )

        llm = get_llm()

        response = await llm.ainvoke(
            prompt
        )

        next_question = (
            response.content.strip()
            if hasattr(response, "content")
            else str(response).strip()
        )

        return {
            **state,
            "next_question": next_question,
            "error": None,
        }

    except Exception as e:

        return {
            **state,
            "error": str(e),
        }