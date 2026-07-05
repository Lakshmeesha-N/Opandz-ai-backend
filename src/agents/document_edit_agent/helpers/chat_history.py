import logging
from typing import Dict, Any

def fetch_chat_history(document_id: str) -> list:
    from src.core import firebase
    firebase.ensure_globals()
    db = firebase.db
    if not document_id or not db:
        return []
    try:
        doc_ref = db.collection("document_chats").document(document_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict().get("messages", [])
    except Exception:
        logging.exception("Failed to fetch chat history from Firestore")
    return []


def save_chat_history(document_id: str, result: Dict[str, Any]):
    from src.core import firebase
    firebase.ensure_globals()
    db = firebase.db
    if not document_id or not db or "messages" not in result:
        return
    try:
        clean_messages = []
        for m in result["messages"]:
            m_type = getattr(m, "type", "")
            if m_type in ("system", "tool"):
                continue
            if m_type == "ai" and getattr(m, "tool_calls", None):
                continue
            content = getattr(m, "content", "")
            if content:
                clean_messages.append({"role": m_type, "content": str(content)})
        
        # Keep only the last 6 messages (3 complete turns) to prevent orphaned message pairs
        clean_messages = clean_messages[-6:]
        
        db.collection("document_chats").document(document_id).set({
            "messages": clean_messages
        }, merge=True)
    except Exception:
        logging.exception("Failed to save chat history to Firestore")
