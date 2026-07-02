# src/api/generated_document_router.py

import asyncio

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from pydantic import (
    BaseModel,
)

from src.auth.firebase_auth import CurrentUser, get_current_user

from src.utils.get_generated_document import (
    get_generated_document,
)

from src.utils.update_generated_document import (
    update_generated_document,
)

from src.utils.delete_generated_document import (
    delete_generated_document,
)


router = APIRouter(
    prefix="/generated-documents",
    tags=[
        "generated-documents",
    ],
)


class UpdateGeneratedDocumentRequest(
    BaseModel,
):
    generated_docxjs_code: str


@router.get(
    "/{document_id}",
)
async def fetch_generated_document(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):

    document = await asyncio.to_thread(
        get_generated_document,
        document_id,
    )

    if document is None:

        raise HTTPException(
            status_code=404,
            detail="Generated document not found",
        )

    return document


@router.put(
    "/{document_id}",
)
async def save_generated_document(
    document_id: str,
    request: UpdateGeneratedDocumentRequest,
    current_user: CurrentUser = Depends(get_current_user),
):

    await asyncio.to_thread(
        update_generated_document,
        document_id,
        request.generated_docxjs_code,
    )

    return {
        "success": True,
    }


@router.delete(
    "/{document_id}",
)
async def remove_generated_document(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):

    await asyncio.to_thread(
        delete_generated_document,
        document_id,
    )

    return {
        "success": True,
    }


@router.get(
    "/lawyer/{lawyer_id}",
)
async def fetch_documents_by_lawyer(
    lawyer_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    from src.core.firebase import get_db
    from firebase_admin import firestore
    try:
        db = get_db()
        docs = await asyncio.to_thread(
            lambda: list(db.collection("generated_documents")
            .where("lawyer_id", "==", lawyer_id)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .stream())
        )
        document_ids = [doc.id for doc in docs]
        return {
            "lawyer_id": lawyer_id,
            "document_ids": document_ids,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch documents for lawyer: {e}",
        )