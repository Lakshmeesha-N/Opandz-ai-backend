# src/utils/template_storage.py

from typing import Any
from concurrent.futures import ThreadPoolExecutor
import logging

from src.core.config import settings


# Small thread pool for background uploads
_EXECUTOR = ThreadPoolExecutor(max_workers=2)


def _submit_background(fn, *args, **kwargs):
    fut = _EXECUTOR.submit(fn, *args, **kwargs)

    def _cb(f):
        try:
            _ = f.result()
        except Exception as e:
            logging.exception("Background firebase upload failed: %s", e)

    fut.add_done_callback(_cb)


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
    """Save a document blueprint template to Firestore (backgrounded).

    When `settings.LOCAL_TEST` is True we perform the write synchronously so
    test / dev flows can observe files immediately; otherwise the write is
    scheduled on a background thread and this function returns immediately.
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

    def _do_set():
        db.collection("templates").document(template_id).set(document_data)

    if settings.LOCAL_TEST:
        _do_set()
    else:
        _submit_background(_do_set)


def save_document_config(
    template_id: str,
    document_config: Any,
) -> None:
    """Save document config to template (backgrounded similarly to `save_template`)."""
    from src.core import firebase  # lazy import

    firebase.ensure_globals()
    db = firebase.db

    def _do_update():
        db.collection("templates").document(template_id).update(
            {
                "document_config": document_config,
            }
        )

    if settings.LOCAL_TEST:
        _do_update()
    else:
        _submit_background(_do_update)


def save_field_manifest(
    template_id: str,
    field_manifest: Any,
) -> None:
    """Store generated field manifest inside an existing template document (backgrounded)."""
    from src.core import firebase  # lazy import

    firebase.ensure_globals()
    db = firebase.db

    def _do_update():
        db.collection("templates").document(template_id).update(
            {
                "field_manifest": field_manifest,
            }
        )

    if settings.LOCAL_TEST:
        _do_update()
    else:
        _submit_background(_do_update)

