from src.core.firebase import get_db


def get_generated_document(
    document_id: str,
) -> dict | None:

    db = get_db()
    document = (
        db.collection(
            "generated_documents",
        )
        .document(
            document_id,
        )
        .get()
    )

    data = document.to_dict()
    if data and data.get("generated_docxjs_code_url"):
        from src.agents.document_generation_agent.helpers.storage_fallback import read_code_from_storage
        try:
            code = read_code_from_storage(data["generated_docxjs_code_url"])
            data["generated_docxjs_code"] = code
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("Failed to load fallback code from GCS: %s", str(e))
            
    return data