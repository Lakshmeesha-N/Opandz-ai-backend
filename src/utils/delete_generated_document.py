from src.core.firebase import get_db


def delete_generated_document(
    document_id: str,
) -> None:

    db = get_db()
    (
        db.collection(
            "generated_documents",
        )
        .document(
            document_id,
        )
        .delete()
    )