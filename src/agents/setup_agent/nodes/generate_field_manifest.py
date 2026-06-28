# src/agents/setup_agent/nodes/generate_field_manifest.py

import json
from pathlib import Path

from src.core.config import settings
from src.agents.setup_agent.schema.global_state import AgentState

from src.agents.setup_agent.helpers.docx.docx_info_extractor import (
    parse_blueprint,
)

from src.agents.setup_agent.prompts.docx.field_manifest_prompt import (
    generate_field_manifest,
)

from src.agents.setup_agent.utils.template_storage import (
    save_field_manifest,
)

from src.llm.llm import get_llm


def generate_field_manifest_node(state: AgentState) -> AgentState:
    """
    Generate field manifest from document blueprint using LLM.
    """

    try:
        print("[generate_field_manifest] START", {k: state.get(k) for k in ("template_id",)})

        blueprint = state["docx_blueprint"]
        # If blueprint was stored as a list, unwrap the first element.
        if isinstance(blueprint, list):
            print("[generate_field_manifest] Unwrapping blueprint list -> using first element")
            blueprint = blueprint[0]

        # Convert full blueprint into simplified LLM-friendly structure
        parsed_blueprint = parse_blueprint(blueprint)

        # Build field extraction prompt
        prompt = generate_field_manifest(parsed_blueprint)

        # Call configured LLM
        llm = get_llm()
        response = llm.invoke(prompt)

        # Support different LLM return types: object with `.content` or raw string
        if isinstance(response, str):
            field_manifest_str = response
        else:
            field_manifest_str = getattr(response, "content", response)

        # Parse JSON and clean any LLM markdown wrappers
        import re
        cleaned = re.sub(r"^```json\s*", "", field_manifest_str.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        try:
            field_manifest = json.loads(cleaned)
        except Exception:
            field_manifest = json.loads(field_manifest_str)

        template_id = state["template_id"]

        save_field_manifest(
            template_id=template_id,
            field_manifest=field_manifest
        )

        print("[generate_field_manifest] END", {"template_id": template_id})
        return {}
    except Exception as e:
        print("[generate_field_manifest] ERROR", str(e))
        return {"generate_field_manifest_error": str(e)}