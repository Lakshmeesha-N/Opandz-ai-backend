# src/agents/document_edit_agent/nodes/load_document_node.py

import tempfile
import logging

from src.agents.document_edit_agent.sub_agents.document_section_edit.schema.state import (
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
        document_id = state.get("document_id")
        logger.info("[load_document_node] START: loading document_id=%s", document_id)

        document = await load_document(
            document_id=document_id,
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

        # Initialize Messages once for the graph
        from langchain_core.messages import convert_to_messages, HumanMessage
        from src.agents.document_edit_agent.sub_agents.document_section_edit.prompts.system_prompt import get_system_prompt

        messages = state.get("messages", [])
        if messages:
            messages = list(convert_to_messages(messages))
            # Filter empty
            messages = [m for m in messages if str(m.content).strip() or (hasattr(m, "tool_calls") and m.tool_calls)]

        user_content = state.get("user_message", "")
        extracted_content_str = ""
        uploaded_files = state.get("uploaded_files", [])
        
        if uploaded_files:
            from src.agents.case_intake_agent.helpers.extract_all_evidence import extract_all_evidence
            evidences = await extract_all_evidence(uploaded_files)
            for ev in evidences:
                extracted_content_str += f"\n\n--- Attached File: {ev['file_name']} ---\nContent:\n{ev['content']}"

        if extracted_content_str:
            user_content += extracted_content_str

        if user_content.strip():
            messages.append(HumanMessage(content=user_content))
            
        blueprint = document.get("blueprint", "")
        if not messages or getattr(messages[0], "type", "") != "system":
            messages.insert(0, get_system_prompt(blueprint))

        return {
            **state,
            "messages": messages,
            "temp_file_path": temp_file.name,
            "blueprint": blueprint,
            "template_id": document.get("template_id", state.get("template_id")),
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