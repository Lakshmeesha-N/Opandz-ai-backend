# src/agents/document_generation_agent/nodes/store_generated_docxjs_code.py

import uuid
import asyncio
import logging

from src.agents.document_generation_agent.schema.global_state import (
    AgentState,
)

from src.agents.document_generation_agent.helpers.store_generated_docxjs_code import (
    store_generated_docxjs_code,
)

logger = logging.getLogger(__name__)


async def store_generated_docxjs_code_node(
    state: AgentState,
) -> AgentState:

    try:
        document_id = str(
            uuid.uuid4(),
        )
        session_id = state.get("session_id")
        template_id = state.get("template_id")
        lawyer_id = state.get("lawyer_id", "")
        logger.info("[store_generated_docxjs_code_node] START: storing docxjs code. Generated document_id=%s, session_id=%s, template_id=%s, lawyer_id=%s", document_id, session_id, template_id, lawyer_id)

        await asyncio.to_thread(
            store_generated_docxjs_code,
            document_id,
            session_id,
            template_id,
            state["generated_docxjs_code"],
            lawyer_id,
        )

        logger.info("[store_generated_docxjs_code_node] SUCCESS: docxjs code stored successfully for document_id=%s", document_id)
        return {
            **state,
            "document_id": document_id,
            "error": None,
        }

    except Exception as e:
        logger.exception("[store_generated_docxjs_code_node] ERROR: %s", str(e))
        return {
            **state,
            "error": str(e),
        }