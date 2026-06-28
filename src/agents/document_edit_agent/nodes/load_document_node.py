# src/agents/document_edit_agent/nodes/load_document_node.py

import tempfile

from src.agents.document_edit_agent.schema.global_state import (
    AgentState,
)

from src.agents.document_edit_agent.helpers.load_document import (
    load_document,
)


async def load_document_node(
    state: AgentState,
) -> AgentState:

    try:

        document = await load_document(
            template_id=state[
                "template_id"
            ],
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

        return {
            **state,
            "error": str(
                e,
            ),
        }