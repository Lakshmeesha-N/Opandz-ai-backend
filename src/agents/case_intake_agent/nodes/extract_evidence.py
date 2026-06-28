# src/agents/case_intake_agent/nodes/extract_evidence.py

from src.agents.case_intake_agent.schema.global_state import (
    AgentState,
)

from src.agents.case_intake_agent.helpers.extract_all_evidence import (
    extract_all_evidence,
)


async def extract_evidence(
    state: AgentState,
) -> AgentState:
    """
    Extract evidence from all uploaded files.

    Input:
        state["uploaded_files"]

    Output:
        state["extracted_evidence"]
    """

    try:

        uploaded_files = state.get(
            "uploaded_files",
            [],
        )

        extracted_evidence = (
            await extract_all_evidence(
                uploaded_files
            )
        )

        return {
            **state,
            "extracted_evidence": extracted_evidence,
            "error": None,
        }

    except Exception as e:

        return {
            **state,
            "error": str(e),
        }