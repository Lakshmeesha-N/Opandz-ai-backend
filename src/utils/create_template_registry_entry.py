# src/agents/setup_agent/helpers/create_template_registry_entry.py

from datetime import datetime


from src.core.firebase import db

def create_template_registry_entry(
    template_id: str,
    lawyer_id: str,
    vault_name: str,
    template_name: str,
) -> None:

    db.collection(
        "template_registry",
    ).document(
        template_id,
    ).set(
        {
            "template_id": template_id,
            "lawyer_id": lawyer_id,
            "vault_name": vault_name,
            "template_name": template_name,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
    )