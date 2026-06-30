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
            messages = convert_to_messages(messages)

        if not messages:
            user_content = state.get("user_message", "")
            if extracted_content_str:
                user_content += extracted_content_str
            logger.info("[document_edit_agent_node] Initializing conversation with user content size: %d", len(user_content))
            messages = [
                get_system_prompt(
                    state["document_config"],
                ),
                HumanMessage(
                    content=user_content,
                ),
            ]
        elif extracted_content_str:
            logger.info("[document_edit_agent_node] Appending attached files content to the last user message")
            if messages and hasattr(messages[-1], "content") and messages[-1].type == "human":
                messages[-1].content = str(messages[-1].content) + extracted_content_str

        logger.info("[document_edit_agent_node] Invoking document edit LLM with %d messages", len(messages))
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