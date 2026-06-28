# src/agents/document_generation_agent/nodes/validate_generated_docxjs_code.py

from src.agents.document_generation_agent.schema.global_state import (
    AgentState,
)

from src.agents.document_generation_agent.helpers.validate_docxjs_code import (
    validate_docxjs_code,
)


async def validate_generated_docxjs_code(
    state: AgentState,
) -> AgentState:

    try:

        generated_code = state.get(
            "generated_docxjs_code",
            "",
        )

        is_valid, validation_error = (
            validate_docxjs_code(
                generated_code,
            )
        )

        if not is_valid:

            return {
                **state,
                "error": validation_error,
            }

        return {
            **state,
            "error": None,
        }

    except Exception as e:

        return {
            **state,
            "error": str(e),
        }