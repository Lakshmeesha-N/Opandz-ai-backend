from src.core.firebase import get_db


def delete_generated_document(
    document_id: str,
) -> None:

    db = get_db()
    doc_ref = db.collection("generated_documents").document(document_id)
    snapshot = doc_ref.get()
    if snapshot.exists:
        data = snapshot.to_dict()
        gcs_uri = data.get("generated_docxjs_code_url")
        if gcs_uri:
            try:
                without_scheme = gcs_uri[len("gs://"):]
                bucket_name, _, blob_path = without_scheme.partition("/")
                if bucket_name == "local-mock":
                    from pathlib import Path
                    local_path = Path("temp") / "storage_fallback" / blob_path
                    local_path.unlink(missing_ok=True)
                else:
                    from src.core import firebase
                    firebase.ensure_globals()
                    bucket = firebase.bucket
                    if bucket:
                        blob = bucket.blob(blob_path)
                        blob.delete()
            except Exception as e:
                import logging
                logging.getLogger(__name__).error("Failed to delete fallback GCS file during delete: %s", str(e))
        doc_ref.delete()