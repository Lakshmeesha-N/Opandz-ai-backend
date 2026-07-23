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

        source = template_data.get("document_blueprint_source", "docx")
        blueprint_content = template_data.get("blueprint_markdown", template_data.get("blueprint", ""))

        if source == "gcs" and template_data.get("blueprint_url"):
            try:
                from src.agents.document_generation_agent.helpers.storage_fallback import read_code_from_storage
                blueprint_content = read_code_from_storage(template_data["blueprint_url"])
            except Exception as ex:
                import logging
                logging.getLogger(__name__).warning("Failed to fetch blueprint from GCS URL: %s", ex)

        return {
            **state,
            "case_data": intake_data.get(
                "case_data",
                {},
            ),
            "blueprint": blueprint_content,
            "document_blueprint_source": source,
            "error": None,
            "validation_retries": 0,
        }


    except Exception as e:

        return {
            **state,
            "error": str(e),
        }