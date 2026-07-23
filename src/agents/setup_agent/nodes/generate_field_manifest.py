# src/agents/setup_agent/nodes/generate_field_manifest.py

import json
import logging
import re

from src.agents.setup_agent.schema.global_state import AgentState
from src.agents.setup_agent.helpers.docx.docx_info_extractor import (
    extract_plain_text,
)
from src.agents.setup_agent.prompts.docx.field_manifest_prompt import (
    generate_field_manifest,
)
from src.agents.setup_agent.utils.template_storage import (
    save_field_manifest,
)
from src.agents.setup_agent.helpers.docx.llm_helpers import (
    invoke_llm_with_retries,
)

logger = logging.getLogger(__name__)


def generate_field_manifest_node(state: AgentState) -> AgentState:
    """
    Generate field manifest independently from the original document blueprint text using LLM.
    """

    try:
        template_id = state["template_id"]
        logger.info("[generate_field_manifest] START: template_id=%s", template_id)

        blueprint = state["docx_blueprint"]
        if isinstance(blueprint, list) and len(blueprint) > 0:
            blueprint = blueprint[0]

        # ── 1. Extract plain text directly from original docx blueprint ──
        document_text = extract_plain_text(blueprint)

        # ── 2. Build field extraction prompt ──
        prompt = generate_field_manifest(document_text)

        # ── 3. Invoke LLM ──
        logger.info("[generate_field_manifest] Invoking LLM...")
        raw_response = invoke_llm_with_retries(prompt)

        # Clean markdown code block wrappers (```json ... ```)
        cleaned = re.sub(r"^```(?:json)?\s*\n?", "", raw_response.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r"\n?\s*```$", "", cleaned).strip()

        try:
            field_manifest = json.loads(cleaned)
        except Exception:
            field_manifest = json.loads(raw_response)

        # ── 4. Store field manifest in Firestore ──
        save_field_manifest(
            template_id=template_id,
            field_manifest=field_manifest,
        )

        logger.info("[generate_field_manifest] END: template_id=%s", template_id)
        return {"error": None}
    except Exception as e:
        logger.exception("[generate_field_manifest] ERROR: %s", str(e))
        return {"error": f"generate_field_manifest failed: {str(e)}"}
