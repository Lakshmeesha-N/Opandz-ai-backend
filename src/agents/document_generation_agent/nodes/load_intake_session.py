# src/agents/document_generation_agent/nodes/load_generation_context.py

import asyncio

from src.agents.document_generation_agent.schema.global_state import (
    AgentState,
)

from src.agents.document_generation_agent.helpers.firestore_loader import (
    get_intake_session,
    get_template,
)


async def load_generation_context(
    state: AgentState,
) -> AgentState:

    try:

        session_id = state["session_id"]
        template_id = state["template_id"]

        intake_task = asyncio.to_thread(
            get_intake_session,
            session_id,
        )

        template_task = asyncio.to_thread(
            get_template,
            template_id,
        )

        (
            intake_data,
            template_data,
        ) = await asyncio.gather(
            intake_task,
            template_task,
        )

        return {
            **state,
            "case_data": intake_data.get(
                "case_data",
                {},
            ),
            "blueprint": template_data.get(
                "blueprint",
                {},
            ),
            "document_config": template_data.get(
                "document_config",
                {},
            ),
            "document_blueprint_source": (
                template_data.get(
                    "document_blueprint_source",
                    "docx",
                )
            ),
            "error": None,
        }

    except Exception as e:

        return {
            **state,
            "error": str(e),
        }