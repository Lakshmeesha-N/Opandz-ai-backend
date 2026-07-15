# src/agents/document_edit_agent/nodes/document_section_edit_node.py

import logging
from langchain_core.messages import (
    HumanMessage,
)

from src.agents.document_edit_agent.sub_agents.document_section_edit.schema.state import (
    AgentState,
)

from src.agents.document_edit_agent.sub_agents.document_section_edit.prompts.system_prompt import (
    get_system_prompt,
)

from src.llm.document_edit_llm import (
    document_edit_llm,
)

logger = logging.getLogger(__name__)


async def document_section_edit_node(
    state: AgentState,
) -> AgentState:

    try:
        logger.info("[document_section_edit_node] START")

        messages = state.get(
            "messages",
            [],
        )

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
            if getattr(m, "name", None) == "validate_docxjs":
                content_str = str(getattr(m, "content", ""))
                import json
                try:
                    res = json.loads(content_str)
                    if isinstance(res, dict) and res.get("valid") is True:
                        last_validation_failed = False
                    else:
                        last_validation_failed = True
                        last_validation_error = content_str
                except Exception:
                    # Fallback if not valid JSON
                    if "error" in content_str.lower() and "error\": null" not in content_str.lower():
                        last_validation_failed = True
                        last_validation_error = content_str
                    else:
                        last_validation_failed = False

        if validation_calls >= settings.doc_edit_max_retries and last_validation_failed:
            logger.error("[document_section_edit_node] Max validation attempts reached. Error: %s", last_validation_error)
            raise ValueError(f"Max validation attempts ({settings.doc_edit_max_retries}) reached. Final error: {last_validation_error}")

        logger.info("[document_section_edit_node] Invoking document edit LLM with %d messages (validation_attempts=%d/%d)", len(messages), validation_calls, settings.doc_edit_max_retries)
        response = await document_edit_llm.ainvoke(
            messages,
        )
        logger.info("[document_section_edit_node] LLM call complete")

        return {
            "messages": [response],
            "error": None,
        }

    except Exception as e:
        logger.exception("[document_section_edit_node] ERROR: %s", str(e))
        return {
            **state,
            "error": str(
                e,
            ),
        }