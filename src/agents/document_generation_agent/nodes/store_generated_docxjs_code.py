# src/agents/document_generation_agent/nodes/store_generated_docxjs_code.py

import uuid
import asyncio

from src.agents.document_generation_agent.schema.global_state import (
    AgentState,
)

from src.agents.document_generation_agent.helpers.store_generated_docxjs_code import (
    store_generated_docxjs_code,
)


async def store_generated_docxjs_code_node(
    state: AgentState,
) -> AgentState:

    try:

        document_id = str(
            uuid.uuid4(),
        )

        await asyncio.to_thread(
            store_generated_docxjs_code,
            document_id,
            state["session_id"],
            state["template_id"],
            state["generated_docxjs_code"],
        )

        return {
            **state,
            "document_id": document_id,
            "error": None,
        }

    except Exception as e:

        return {
            **state,
            "error": str(e),
        }