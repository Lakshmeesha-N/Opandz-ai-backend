# src/agents/document_generation_agent/nodes/validate_generated_docxjs_code.py

import logging
from src.agents.document_generation_agent.schema.global_state import (
    AgentState,
)

from src.agents.document_generation_agent.helpers.validate_docxjs_code import (
    validate_docxjs_code,
)

logger = logging.getLogger(__name__)


async def validate_generated_docxjs_code(
    state: AgentState,
) -> AgentState:

    try:
        logger.info("[validate_generated_docxjs_code] START: validating generated code")

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
            logger.warning("[validate_generated_docxjs_code] Validation FAILED: %s", validation_error)
            return {
                **state,
                "error": validation_error,
            }

        logger.info("[validate_generated_docxjs_code] Validation SUCCESS")
        return {
            **state,
            "error": None,
        }

    except Exception as e:
        logger.exception("[validate_generated_docxjs_code] ERROR: %s", str(e))
        return {
            **state,
            "error": str(e),
        }