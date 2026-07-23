# nodes/merge_and_upload.py

import logging
import os

from src.agents.setup_agent.schema.global_state import AgentState

logger = logging.getLogger(__name__)


def merge_and_upload(state: AgentState) -> AgentState:
    """
    Merge the blueprint_metadata.md and blueprint_body.md into a single
    combined markdown document, then upload it to Firestore under the
    template document's `blueprint_markdown` field.
    """

    try:
        temp_dir = state["temp_dir"]
        template_id = state["template_id"]
        lawyer_id = state["lawyer_id"]

        logger.info(
            "[merge_and_upload] START: template_id=%s", template_id
        )

        # ── 1. Read the two generated markdowns ──
        metadata_path = os.path.join(temp_dir, "blueprint_metadata.md")
        body_path = os.path.join(temp_dir, "blueprint_body.md")

        metadata_md = ""
        if os.path.exists(metadata_path):
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata_md = f.read()
        else:
            logger.warning(
                "[merge_and_upload] blueprint_metadata.md not found at %s",
                metadata_path,
            )

        body_md = ""
        if os.path.exists(body_path):
            with open(body_path, "r", encoding="utf-8") as f:
                body_md = f.read()
        else:
            logger.warning(
                "[merge_and_upload] blueprint_body.md not found at %s",
                body_path,
            )

        from src.agents.setup_agent.helpers.docx.llm_helpers import clean_markdown_text

        metadata_md = clean_markdown_text(metadata_md)
        body_md = clean_markdown_text(body_md)

        # ── 2. Merge into a single markdown ──
        merged_md = (
            "# Blueprint Metadata\n\n"
            f"{metadata_md}\n\n"
            "---\n\n"
            "# Blueprint Body\n\n"
            f"{body_md}\n"
        )

        # ── 3. Upload to Firestore ──
        from src.core import firebase  # lazy import

        firebase.ensure_globals()
        db = firebase.db

        db.collection("templates").document(template_id).set({
            "template_id": template_id,
            "lawyer_id": lawyer_id,
            "blueprint_markdown": merged_md,
        }, merge=True)

        logger.info(
            "[merge_and_upload] END: uploaded blueprint_markdown for template_id=%s",
            template_id,
        )

        return {"error": None}

    except Exception as e:
        logger.exception("[merge_and_upload] ERROR: %s", str(e))
        return {"error": f"merge_and_upload failed: {str(e)}"}
