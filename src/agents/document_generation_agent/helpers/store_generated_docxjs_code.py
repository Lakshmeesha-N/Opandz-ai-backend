# src/agents/document_generation_agent/helpers/store_generated_docxjs_code.py

from datetime import datetime

from src.core.firebase import get_db



def store_generated_docxjs_code(
    document_id: str,
    session_id: str,
    template_id: str,
    generated_docxjs_code: str,
    lawyer_id: str = "",
) -> None:

    try:
        db = get_db()
        db.collection(
            "generated_documents",
        ).document(
            document_id,
        ).set(
            {
                "document_id": document_id,
                "session_id": session_id,
                "template_id": template_id,
                "lawyer_id": lawyer_id,
                "generated_docxjs_code": generated_docxjs_code,
                "version": 1,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Firestore write failed. Falling back to GCS upload: %s", str(e))
        
        from src.agents.document_generation_agent.helpers.storage_fallback import upload_code_to_storage
        gcs_uri = upload_code_to_storage(template_id, document_id, generated_docxjs_code)
        
        db = get_db()
        db.collection(
            "generated_documents",
        ).document(
            document_id,
        ).set(
            {
                "document_id": document_id,
                "session_id": session_id,
                "template_id": template_id,
                "lawyer_id": lawyer_id,
                "generated_docxjs_code": "",  # Stub empty
                "generated_docxjs_code_url": gcs_uri,
                "version": 1,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )