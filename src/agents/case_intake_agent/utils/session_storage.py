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