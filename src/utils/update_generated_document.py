from datetime import datetime

from src.core.firebase import get_db


def update_generated_document(
    document_id: str,
    generated_docxjs_code: str,
) -> None:

    db = get_db()
    document_ref = (
        db.collection(
            "generated_documents",
        )
        .document(
            document_id,
        )
    )

    snapshot = document_ref.get()

    if not snapshot.exists:

        raise ValueError(
            "Generated document not found",
        )

    document = snapshot.to_dict()

    try:
        gcs_uri = document.get("generated_docxjs_code_url")
        if gcs_uri:
            # Write directly to existing GCS path
            from src.agents.document_generation_agent.helpers.storage_fallback import upload_code_to_storage
            upload_code_to_storage(document.get("template_id", "fallback"), document_id, generated_docxjs_code)
            document_ref.update(
                {
                    "generated_docxjs_code": "",
                    "version": document.get("version", 1) + 1,
                    "updated_at": datetime.utcnow(),
                }
            )
        else:
            # Try writing to Firestore
            document_ref.update(
                {
                    "generated_docxjs_code": generated_docxjs_code,
                    "version": document.get("version", 1) + 1,
                    "updated_at": datetime.utcnow(),
                }
            )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Firestore update failed. Falling back to GCS: %s", str(e))
        from src.agents.document_generation_agent.helpers.storage_fallback import upload_code_to_storage
        gcs_uri = upload_code_to_storage(document.get("template_id", "fallback"), document_id, generated_docxjs_code)
        document_ref.update(
            {
                "generated_docxjs_code": "",
                "generated_docxjs_code_url": gcs_uri,
                "version": document.get("version", 1) + 1,
                "updated_at": datetime.utcnow(),
            }
        )