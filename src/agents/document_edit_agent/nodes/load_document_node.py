# src/agents/document_edit_agent/nodes/load_document_node.py

import tempfile
import logging

from src.agents.document_edit_agent.schema.global_state import (
    AgentState,
)

from src.agents.document_edit_agent.helpers.load_document import (
    load_document,
)

logger = logging.getLogger(__name__)


async def load_document_node(
    state: AgentState,
) -> AgentState:

    try:
        template_id = state.get("template_id")
        logger.info("[load_document_node] START: loading template_id=%s", template_id)

        document = await load_document(
            template_id=template_id,
        )

        temp_file = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".js",
            delete=False,
            encoding="utf-8",
        )

        temp_file.write(
            document[
                "generated_docxjs_code"
            ],
        )

        temp_file.close()
        logger.info("[load_document_node] SUCCESS: loaded docxjs code and saved to temp_file=%s", temp_file.name)

        return {
            **state,
            "temp_file_path": temp_file.name,
            "document_config": document[
                "document_config"
            ],
            "blueprint": document[
                "blueprint"
            ],
            "error": None,
        }

    except Exception as e:
        logger.exception("[load_document_node] ERROR: %s", str(e))
        return {
            **state,
            "error": str(
                e,
            ),
        }