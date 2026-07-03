# src/agents/document_edit_agent/helpers/load_document.py

import asyncio

from src.core.firebase import get_db

from src.agents.document_edit_agent.helpers.docs_config_cleaner import (
    build_llm_document_context,
)


async def load_document(
    document_id: str,
) -> dict:

    document_data = await asyncio.to_thread(
        _load_generated_document,
        document_id,
    )

    template_id = document_data.get("template_id")
    if not template_id:
        raise ValueError("template_id not found in generated document")

    template_data = await asyncio.to_thread(
        _load_template,
        template_id,
    )

    document_config = build_llm_document_context(
        template_data.get(
            "document_config",
            {},
        ),
    )

    return {
        "generated_docxjs_code": document_data.get(
            "generated_docxjs_code",
            "",
        ),
        "document_config": document_config,
        "blueprint": template_data.get(
            "blueprint",
            {},
        ),
        "template_id": template_id,
    }


def _load_generated_document(
    document_id: str,
) -> dict:

    db = get_db()
    document_ref = (
        db.collection(
            "generated_documents",
        )
        .document(
            document_id,
        )
        .get()
    )

    if not document_ref.exists:

        raise ValueError(
            "Generated document not found",
        )

    data = document_ref.to_dict()
    if data and data.get("generated_docxjs_code_url"):
        from src.agents.document_generation_agent.helpers.storage_fallback import read_code_from_storage
        try:
            code = read_code_from_storage(data["generated_docxjs_code_url"])
            data["generated_docxjs_code"] = code
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("Failed to load fallback code from GCS: %s", str(e))

    return data


def _load_template(
    template_id: str,
) -> dict:

    db = get_db()
    template_ref = (
        db.collection(
            "templates",
        )
        .document(
            template_id,
        )
        .get()
    )

    if not template_ref.exists:

        raise ValueError(
            "Template not found",
        )

    return template_ref.to_dict()