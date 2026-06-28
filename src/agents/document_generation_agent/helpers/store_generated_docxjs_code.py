# src/agents/document_generation_agent/helpers/store_generated_docxjs_code.py

from datetime import datetime

from src.core.firebase import db



def store_generated_docxjs_code(
    document_id: str,
    session_id: str,
    template_id: str,
    generated_docxjs_code: str,
) -> None:

    db.collection(
        "generated_documents",
    ).document(
        document_id,
    ).set(
        {
            "document_id": document_id,
            "session_id": session_id,
            "template_id": template_id,
            "generated_docxjs_code": generated_docxjs_code,
            "version": 1,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
    )