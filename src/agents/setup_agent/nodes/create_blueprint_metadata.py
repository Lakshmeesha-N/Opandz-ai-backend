# nodes/create_blueprint_metadata.py

import json
import logging
import os

from src.agents.setup_agent.schema.global_state import AgentState
from src.agents.setup_agent.prompts.docx.blueprint_metadata_prompt import prompt as BLUEPRINT_METADATA_PROMPT
from src.agents.setup_agent.helpers.docx.llm_helpers import (
    read_file,
    extract_section_metadata,
    invoke_llm_with_retries,
    clean_markdown_text,
)

logger = logging.getLogger(__name__)


def create_blueprint_metadata(state: AgentState) -> AgentState:
    """
    Generate the layout / style specification markdown from:
      - the parsed JSON blueprint (section metadata)
      - the raw XML files (styles, numbering, theme, fontTable)

    Saves the result to <temp_dir>/blueprint_metadata.md.
    """

    try:
        temp_dir = state["temp_dir"]
        template_id = state["template_id"]

        logger.info(
            "[create_blueprint_metadata] START: template_id=%s", template_id
        )

        # ── 1. Build JSON_METADATA from the parsed blueprint ──
        blueprint = state["docx_blueprint"]
        if isinstance(blueprint, list) and len(blueprint) > 0:
            blueprint = blueprint[0]

        sections = extract_section_metadata(blueprint)
        json_metadata = json.dumps(sections, indent=2)

        # ── 2. Read XML files from the unzipped temp directory ──
        word_dir = os.path.join(temp_dir, "word")

        xml_data = ""
        for label, rel_path in [
            ("theme1.xml", os.path.join("theme", "theme1.xml")),
            ("styles.xml", "styles.xml"),
            ("numbering.xml", "numbering.xml"),
            ("fontTable.xml", "fontTable.xml"),
        ]:
            full_path = os.path.join(word_dir, rel_path)
            content = read_file(full_path)
            xml_data += f"--- {label} ---\n{content}\n\n"

        # ── 3. Assemble the prompt ──
        final_prompt = (
            f"{BLUEPRINT_METADATA_PROMPT}\n\n"
            f"### JSON_METADATA ###\n{json_metadata}\n\n"
            f"### XML_DATA ###\n{xml_data}"
        )

        # ── 4. Invoke LLM ──
        logger.info("[create_blueprint_metadata] Invoking LLM...")
        markdown_text = clean_markdown_text(invoke_llm_with_retries(final_prompt))

        # ── 5. Save to temp directory ──
        md_path = os.path.join(temp_dir, "blueprint_metadata.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)

        logger.info(
            "[create_blueprint_metadata] END: saved to %s", md_path
        )

        return {"error": None}

    except Exception as e:
        logger.exception("[create_blueprint_metadata] ERROR: %s", str(e))
        return {"error": f"create_blueprint_metadata failed: {str(e)}"}
