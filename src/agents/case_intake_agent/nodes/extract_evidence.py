# src/agents/case_intake_agent/nodes/extract_evidence.py

import logging

from src.agents.case_intake_agent.schema.global_state import (
    AgentState,
)

from src.agents.case_intake_agent.helpers.extract_all_evidence import (
    extract_all_evidence,
)

logger = logging.getLogger(__name__)


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

    if state.get("error"):
        return state

    try:

        uploaded_files = state.get(
            "uploaded_files",
            [],
        )

        logger.info("[extract_evidence] START: processing %d files", len(uploaded_files))

        extracted_evidence = (
            await extract_all_evidence(
                uploaded_files
            )
        )

        logger.info("[extract_evidence] SUCCESS: extracted evidence from %d files", len(uploaded_files))

        return {
            **state,
            "extracted_evidence": extracted_evidence,
            "error": None,
        }

    except Exception as e:

        logger.exception("[extract_evidence] ERROR: %s", str(e))

        return {
            **state,
            "error": str(e),
        }