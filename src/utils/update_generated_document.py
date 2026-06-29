from datetime import datetime

from src.core.firebase import get_db


def update_generated_document(
    document_id: str,
    generated_docxjs_code: str,
) -> None:

    db = get_db()
    document_ref = (
        db.collection(
            "generated_documents",
        )
        .document(
            document_id,
        )
    )

    snapshot = document_ref.get()

    if not snapshot.exists:

        raise ValueError(
            "Generated document not found",
        )

    document = snapshot.to_dict()

    document_ref.update(
        {
            "generated_docxjs_code": generated_docxjs_code,
            "version": document.get(
                "version",
                1,
            )
            + 1,
            "updated_at": datetime.utcnow(),
        },
    )