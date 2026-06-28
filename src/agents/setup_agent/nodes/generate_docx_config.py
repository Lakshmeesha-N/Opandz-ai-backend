import json
from pathlib import Path

from src.core.config import settings
from src.agents.setup_agent.schema.global_state import AgentState
from src.agents.setup_agent.helpers.docx.docx_info_extractor import (
    parse_blueprint,
)
from src.agents.setup_agent.prompts.docx.layout_prompt_builder import (
    create_layout_prompt,
)
from src.agents.setup_agent.utils.template_storage import (
    save_document_config,
)
from src.llm.llm import get_llm


def generate_docx_config(state: AgentState) -> AgentState:
    """
    Generate document configuration using the blueprint and LLM.
    """

    try:
        print("[generate_docx_config] START", {k: state.get(k) for k in ("template_id",)})

        blueprint = state["docx_blueprint"]
        # If blueprint was stored as a list (templates/... json stores sections as list),
        # unwrap the first element to preserve original blueprint structure.
        if isinstance(blueprint, list):
            print("[generate_docx_config] Unwrapping blueprint list -> using first element")
            blueprint = blueprint[0]

        # Simplify blueprint for LLM
        parsed_blueprint = parse_blueprint(blueprint)

        # Create prompt
        prompt = create_layout_prompt(parsed_blueprint)

        # Call LLM
        llm = get_llm()
        response = llm.invoke(prompt)

        # Support different LLM return types: object with `.content` or raw string
        if isinstance(response, str):
            document_config_str = response
        else:
            document_config_str = getattr(response, "content", response)

        # Parse JSON and clean any LLM markdown wrappers
        import re
        cleaned = re.sub(r"^```json\s*", "", document_config_str.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        try:
            document_config = json.loads(cleaned)
        except Exception:
            document_config = json.loads(document_config_str)

        template_id = state["template_id"]

        # Save to database (under local testing, this writes to the local mock Firestore)
        save_document_config(
            template_id=template_id,
            document_config=document_config
        )

        print("[generate_docx_config] END", {"template_id": template_id})
        return {}
    except Exception as e:
        print("[generate_docx_config] ERROR", str(e))
        return {"generate_docx_config_error": str(e)}