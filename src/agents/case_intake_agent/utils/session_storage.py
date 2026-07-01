# src/agents/case_intake_agent/utils/session_storage.py
from src.core.firebase import get_db



def save_intake_session(

    session_id: str,

    document_data: dict,

) -> None:

    """

    Synchronous Firestore write.

    Runs inside a worker thread.

    """

    db = get_db()
    db.collection(

        "intake_sessions"

    ).document(

        session_id

    ).set(

        document_data,

        merge=True,

    )


def get_intake_session(
    session_id: str,
) -> dict:
    """
    Synchronous Firestore read.
    Runs inside a worker thread.
    """
    db = get_db()
    doc = db.collection("intake_sessions").document(session_id).get()
    return doc.to_dict() if doc.exists else {}