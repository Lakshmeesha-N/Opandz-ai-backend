# src/agents/document_generation_agent/helpers/firestore_loader.py

from src.core.firebase import db

def get_intake_session(session_id: str) -> dict:
    """Fetch an intake session document by ID."""
    doc = (
        db.collection("intake_sessions")
        .document(session_id)
        .get()
    )

    if not doc.exists:
        raise ValueError(f"Session not found: {session_id}")

    return doc.to_dict()


def get_template(template_id: str) -> dict:
    """Fetch a template document by ID."""
    doc = (
        db.collection("templates")
        .document(template_id)
        .get()
    )

    if not doc.exists:
        raise ValueError(f"Template not found: {template_id}")

    return doc.to_dict()
