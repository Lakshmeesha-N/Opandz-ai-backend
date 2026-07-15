# src/agents/document_edit_agent/nodes/router_node.py

import logging
from typing import Literal

from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from src.agents.document_edit_agent.schema.state import DocumentEditState
from src.agents.document_edit_agent.prompts.router_prompt import ROUTER_SYSTEM_PROMPT
from src.core.config import settings
from src.llm.llm import get_llm

logger = logging.getLogger(__name__)


class RouterDecision(BaseModel):
    """The router's classification of the user's intent."""
    next_agent: Literal["editor", "assistant"] = Field(
        description="'editor' if the user wants to modify the document, 'assistant' if they want to ask a question about it."
    )


async def router_node(state: DocumentEditState) -> dict:
    """
    Uses an LLM with structured output to classify the user's message
    as either an 'editor' or 'assistant' intent.
    """
    try:
        logger.info("[router_node] START — classifying user intent")

        user_message = state.get("user_message", "")
        if not user_message:
            logger.warning("[router_node] No user_message found, defaulting to assistant")
            return {"next_agent": "assistant"}

        llm = get_llm(model_name=settings.router_model)

        # Use with_structured_output for reliable JSON classification
        structured_llm = llm._client.with_structured_output(RouterDecision)

        messages = [
            ROUTER_SYSTEM_PROMPT,
            HumanMessage(content=user_message),
        ]

        decision: RouterDecision = structured_llm.invoke(messages)

        logger.info(
            "[router_node] END — user_message=%r → next_agent=%s",
            user_message[:80],
            decision.next_agent,
        )

        return {"next_agent": decision.next_agent}

    except Exception as e:
        logger.exception("[router_node] ERROR: %s — defaulting to assistant", e)
        return {"next_agent": "assistant", "error": str(e)}
