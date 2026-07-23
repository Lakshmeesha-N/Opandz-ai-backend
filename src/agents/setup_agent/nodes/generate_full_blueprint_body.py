# nodes/generate_full_blueprint_body.py

import json
import logging
import os

from src.agents.setup_agent.schema.global_state import AgentState
from src.agents.setup_agent.prompts.docx.blueprint_body_prompt import prompt as BLUEPRINT_BODY_PROMPT
from src.agents.setup_agent.helpers.docx.llm_helpers import (
    invoke_llm_with_retries,
    clean_markdown_text,
)

logger = logging.getLogger(__name__)


def generate_full_blueprint_body(state: AgentState) -> AgentState:
    """
    Generate the full reconstructed document body markdown from the
    parsed JSON blueprint.

    Saves the result to <temp_dir>/blueprint_body.md.
    """

    try:
        temp_dir = state["temp_dir"]
        template_id = state["template_id"]

        logger.info(
            "[generate_full_blueprint_body] START: template_id=%s",
            template_id,
        )

        # ── 1. Get the blueprint JSON ──
        blueprint = state["docx_blueprint"]
        if isinstance(blueprint, list) and len(blueprint) > 0:
            blueprint = blueprint[0]

        json_string = json.dumps(blueprint, indent=2)

        # ── 2. Assemble the prompt ──
        final_prompt = (
            f"{BLUEPRINT_BODY_PROMPT}\n\n"
            f"### FULL_JSON ###\n{json_string}"
        )

        # ── 3. Invoke LLM ──
        logger.info("[generate_full_blueprint_body] Invoking LLM...")
        markdown_text = clean_markdown_text(invoke_llm_with_retries(final_prompt))

        # ── 4. Save to temp directory ──
        md_path = os.path.join(temp_dir, "blueprint_body.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)

        logger.info(
            "[generate_full_blueprint_body] END: saved to %s", md_path
        )

        return {"error": None}

    except Exception as e:
        logger.exception(
            "[generate_full_blueprint_body] ERROR: %s", str(e)
        )
        return {"error": f"generate_full_blueprint_body failed: {str(e)}"}
