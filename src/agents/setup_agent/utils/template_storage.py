# src/utils/template_storage.py

from typing import Any
import logging

from src.core.config import settings


def sanitize_keys(data: Any) -> Any:
    """Recursively replace characters in dict keys that are invalid in Firestore."""
    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            # Replace invalid characters: . , / \ [ ] *
            new_key = (
                str(k)
                .replace(".", "_")
                .replace("/", "_")
                .replace("\\", "_")
                .replace("[", "_")
                .replace("]", "_")
                .replace("*", "_")
            )
            # Firestore strictly prohibits keys that start and end with '__' (reserved)
            if new_key.startswith("__") and new_key.endswith("__") and len(new_key) >= 4:
                new_key = "sanitized_" + new_key[2:-2]
                
            if not new_key:
                new_key = "empty_key"
            new_dict[new_key] = sanitize_keys(v)
        return new_dict
    elif isinstance(data, list):
        return [sanitize_keys(x) for x in data]
    return data


def save_template(
    template_id: str,
    lawyer_id: str,
    blueprint: dict,
) -> None:
    """Save a document blueprint template to Firestore synchronously.

    We perform the write synchronously to ensure correct execution order and
    avoid race conditions on background threads.
    """
    from src.core import firebase  # lazy import — avoids GCS connection at module load

    firebase.ensure_globals()
    db = firebase.db

    sanitized_blueprint = sanitize_keys(blueprint)

    document_data = {
        "template_id": template_id,
        "lawyer_id": lawyer_id,
        "blueprint": sanitized_blueprint,
    }

    db.collection("templates").document(template_id).set(document_data)



def save_field_manifest(
    template_id: str,
    field_manifest: Any,
) -> None:
    """Store generated field manifest inside an existing template document synchronously."""
    from src.core import firebase  # lazy import

    firebase.ensure_globals()
    db = firebase.db

    db.collection("templates").document(template_id).update(
        {
            "field_manifest": field_manifest,
        }
    )

