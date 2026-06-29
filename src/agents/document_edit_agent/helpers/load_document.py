# src/agents/document_edit_agent/helpers/load_document.py

import asyncio

from src.core.firebase import get_db

from src.agents.document_edit_agent.helpers.docs_config_cleaner import (
    build_llm_document_context,
)


async def load_document(
    template_id: str,
) -> dict:

    document_task = asyncio.to_thread(
        _load_generated_document,
        template_id,
    )

    template_task = asyncio.to_thread(
        _load_template,
        template_id,
    )

    document_data, template_data = await asyncio.gather(
        document_task,
        template_task,
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
    }


def _load_generated_document(
    template_id: str,
) -> dict:

    db = get_db()
    document_ref = (
        db.collection(
            "generated_documents",
        )
        .where(
            "template_id",
            "==",
            template_id,
        )
        .limit(1)
        .stream()
    )

    document = next(
        document_ref,
        None,
    )

    if not document:

        raise ValueError(
            "Generated document not found",
        )

    return document.to_dict()


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