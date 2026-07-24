# src/agents/document_generation_agent/nodes/fix_docxjs_code.py

import logging
from src.agents.document_generation_agent.schema.global_state import (
    AgentState,
)

from src.llm.llm import (
    get_llm,
)

from src.agents.document_generation_agent.prompts.fix_docxjs_code_prompt import (
    create_fix_docxjs_code_prompt,
)

logger = logging.getLogger(__name__)


async def fix_docxjs_code(
    state: AgentState,
) -> AgentState:

    try:
        validation_error = state.get("error")
        logger.info("[fix_docxjs_code] START: attempting to fix code after error: %s", validation_error)

        prompt = create_fix_docxjs_code_prompt(
            generated_code=state.get(
                "generated_docxjs_code",
                "",
            ),
            validation_error=validation_error,
        )

        llm = get_llm()

        response = await llm.ainvoke(
            prompt,
        )

        fixed_code = getattr(
            response,
            "content",
            str(response),
        )

        logger.info("[fix_docxjs_code] SUCCESS: generated fixed code size: %d characters", len(fixed_code))
        retries = state.get("validation_retries", 0) + 1
        return {
            **state,
            "generated_docxjs_code": fixed_code,
            "validation_retries": retries,
            "error": None,
        }


    except Exception as e:
        logger.exception("[fix_docxjs_code] ERROR: %s", str(e))
        retries = state.get("validation_retries", 0) + 1
        return {
            **state,
            "validation_retries": retries,
            "error": str(e),
        }