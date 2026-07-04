# src/agents/document_edit_agent/nodes/document_edit_agent_node.py

import logging
from langchain_core.messages import (
    HumanMessage,
)

from src.agents.document_edit_agent.schema.global_state import (
    AgentState,
)

from src.agents.document_edit_agent.prompts.system_prompt import (
    get_system_prompt,
)

from src.llm.document_edit_llm import (
    document_edit_llm,
)

logger = logging.getLogger(__name__)


async def document_edit_agent_node(
    state: AgentState,
) -> AgentState:

    try:
        logger.info("[document_edit_agent_node] START")

        messages = state.get(
            "messages",
            [],
        )

        uploaded_files = state.get("uploaded_files", [])
        extracted_content_str = ""
        if uploaded_files:
            logger.info("[document_edit_agent_node] Extracting content from %d uploaded files", len(uploaded_files))
            from src.agents.case_intake_agent.helpers.extract_all_evidence import extract_all_evidence
            evidences = await extract_all_evidence(uploaded_files)
            for ev in evidences:
                extracted_content_str += f"\n\n--- Attached File: {ev['file_name']} ---\nContent:\n{ev['content']}"

        from langchain_core.messages import convert_to_messages, HumanMessage
        if messages:
            messages = list(convert_to_messages(messages))
            # Filter out empty messages to prevent Gemini API 'contents are required' error
            messages = [m for m in messages if str(m.content).strip() or (hasattr(m, "tool_calls") and m.tool_calls)]

        if not messages:
            user_content = state.get("user_message", "")
            if extracted_content_str:
                user_content += extracted_content_str
            logger.info("[document_edit_agent_node] Initializing conversation with user content size: %d", len(user_content))
            messages = [
                HumanMessage(
                    content=user_content,
                ),
            ]
        else:
            user_content = state.get("user_message", "")
            if extracted_content_str:
                user_content += extracted_content_str
            if user_content.strip():
                logger.info("[document_edit_agent_node] Appending current user message to history")
                messages.append(HumanMessage(content=user_content))

        # ALWAYS ensure the system prompt is at the beginning
        if not messages or getattr(messages[0], "type", "") != "system":
            messages.insert(0, get_system_prompt(state.get("document_config", {})))

        # Enforce validation attempt limits from config
        from src.core.config import settings
        validation_calls = 0
        last_validation_failed = False
        last_validation_error = None
        for m in messages:
            if hasattr(m, "tool_calls") and m.tool_calls:
                for tc in m.tool_calls:
                    if tc.get("name") == "validate_docxjs":
                        validation_calls += 1
            # Check if this is the ToolMessage response for validate_docxjs
            if getattr(m, "name", None) == "validate_docxjs":
                content_str = str(getattr(m, "content", ""))
                # If there's an error in validation, mark it as failed
                if "error" in content_str.lower() or "exception" in content_str.lower() or "syntaxerror" in content_str.lower() or "fail" in content_str.lower():
                    last_validation_failed = True
                    last_validation_error = content_str
                else:
                    last_validation_failed = False

        if validation_calls >= settings.doc_edit_max_retries and last_validation_failed:
            logger.error("[document_edit_agent_node] Max validation attempts reached. Error: %s", last_validation_error)
            raise ValueError(f"Max validation attempts ({settings.doc_edit_max_retries}) reached. Final error: {last_validation_error}")

        logger.info("[document_edit_agent_node] Invoking document edit LLM with %d messages (validation_attempts=%d/%d)", len(messages), validation_calls, settings.doc_edit_max_retries)
        response = await document_edit_llm.ainvoke(
            messages,
        )
        logger.info("[document_edit_agent_node] LLM call complete")

        return {
            **state,
            "messages": [
                *messages,
                response,
            ],
            "error": None,
        }

    except Exception as e:
        logger.exception("[document_edit_agent_node] ERROR: %s", str(e))
        return {
            **state,
            "error": str(
                e,
            ),
        }