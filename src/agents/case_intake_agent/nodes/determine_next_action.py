# src/agents/case_intake_agent/nodes/determine_next_action.py

from src.agents.case_intake_agent.schema.global_state import (
    AgentState,
)


def determine_next_action(
    state: AgentState,
) -> AgentState:
    """
    Decide what should happen next.

    Outputs:
        next_action:
            - ask_question
            - ready_to_generate
    """

    try:

        completion_percentage = state.get(
            "completion_percentage",
            0.0,
        )

        ready_to_generate = state.get(
            "ready_to_generate",
            False,
        )

        if ready_to_generate:

            next_action = (
                "ready_to_generate"
            )

        else:

            next_action = (
                "ask_question"
            )

        return {
            **state,
            "next_action": next_action,
            "error": None,
        }

    except Exception as e:

        return {
            **state,
            "error": str(e),
        }