# src/agents/document_generation_agent/nodes/generate_docxjs_code.py

import logging
from src.agents.document_generation_agent.schema.global_state import (
    AgentState,
)

from src.agents.document_generation_agent.prompts.create_docxjs_generation_prompt import (
    create_docxjs_generation_prompt,
)

from src.llm.llm import (
    get_llm,
)

logger = logging.getLogger(__name__)


async def generate_docxjs_code(
    state: AgentState,
) -> AgentState:

    try:
        logger.info("[generate_docxjs_code] START: generating docxjs code")

        prompt = create_docxjs_generation_prompt(
            state,
        )

        llm = get_llm()

        response = await llm.ainvoke(
            prompt,
        )

        generated_code = getattr(
            response,
            "content",
            str(response),
        )

        logger.info("[generate_docxjs_code] SUCCESS: generated code size: %d characters", len(generated_code))
        return {
            **state,
            "generated_docxjs_code": generated_code,
            "error": None,
        }

    except Exception as e:
        logger.exception("[generate_docxjs_code] ERROR: %s", str(e))
        return {
            **state,
            "error": str(e),
        }