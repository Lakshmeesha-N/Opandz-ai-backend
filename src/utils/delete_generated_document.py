from src.core.firebase import db


def delete_generated_document(
    document_id: str,
) -> None:

    (
        db.collection(
            "generated_documents",
        )
        .document(
            document_id,
        )
        .delete()
    )