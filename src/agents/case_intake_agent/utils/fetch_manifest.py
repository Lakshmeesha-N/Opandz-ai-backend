# src/agents/case_intake_agent/utils/fetch_manifest.py

import asyncio
from src.core.firebase import get_db


async def get_field_manifest(
    template_id: str,
) -> dict:
    """
    Load field manifest from Firestore.

    Firestore Admin SDK is synchronous,
    so run it in a background thread.
    """

    def _fetch():
        db = get_db()
        doc = (
            db.collection("templates")
            .document(template_id)
            .get()
        )

        if not doc.exists:
            raise ValueError(
                f"Template '{template_id}' not found"
            )

        data = doc.to_dict()

        if "field_manifest" not in data:
            raise ValueError(
                f"Field manifest missing for template '{template_id}'"
            )

        return data["field_manifest"]

    return await asyncio.to_thread(_fetch)