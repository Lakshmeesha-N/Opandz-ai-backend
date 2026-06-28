from src.core.firebase import db


def get_generated_document(
    document_id: str,
) -> dict | None:

    document = (
        db.collection(
            "generated_documents",
        )
        .document(
            document_id,
        )
        .get()
    )

    if not document.exists:
        return None

    return document.to_dict()