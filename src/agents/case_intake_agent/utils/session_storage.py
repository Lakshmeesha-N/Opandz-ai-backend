# src/agents/case_intake_agent/utils/session_storage.py
from firebase_admin import firestore
from src.core.firebase import db



def save_intake_session(

    session_id: str,

    document_data: dict,

) -> None:

    """

    Synchronous Firestore write.

    Runs inside a worker thread.

    """



    db.collection(

        "intake_sessions"

    ).document(

        session_id

    ).set(

        document_data,

        merge=True,

    )