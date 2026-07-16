# src/api/dependencies/plan_limits.py
#
# Reusable FastAPI dependency functions for plan-based limit checks.
#
# Usage in a route:
#   @router.post("/")
#   async def my_endpoint(
#       ...,
#       plan_info: dict = Depends(check_uploaded_file_page_limit),
#   ):
#       ...

import logging
from io import BytesIO
from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import Depends, File, HTTPException, UploadFile, status
from docx import Document

from src.auth.firebase_auth import CurrentUser, get_current_user
from src.core.subscription_config import get_plan_constraints, DEFAULT_PLAN

logger = logging.getLogger(__name__)


def _resolve_active_plan(uid: str) -> str:
    """
    Fetch the user's active plan from Firestore.

    Returns:
        The resolved plan string ("free" or "premium").
    """
    from src.core.firebase import get_db

    db = get_db()
    user_ref = db.collection("users").document(uid)
    user_doc = user_ref.get()

    if not user_doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    user_data = user_doc.to_dict()
    plan = user_data.get("plan", DEFAULT_PLAN)

    return plan


async def check_uploaded_file_page_limit(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    """
    FastAPI dependency that:
    1. Reads the user's plan from Firestore (with auto-downgrade on expiry).
    2. Counts the pages in the uploaded DOCX via core properties metadata.
    3. Rejects with HTTP 403 if pages exceed the plan limit.

    Returns:
        A dict with {"plan": str, "pages": int} for use in the route handler.
    """
    uid = current_user.uid
    plan = _resolve_active_plan(uid)
    constraints = get_plan_constraints(plan)
    max_pages = constraints["max_pages"]

    # Read file bytes for page count
    file_bytes = await file.read()
    await file.seek(0)  # Reset so the route handler can read the file again

    filename = file.filename or ""
    try:
        if filename.lower().endswith(".pdf"):
            import fitz
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            pages = doc.page_count
        else:
            doc = Document(BytesIO(file_bytes))
            pages = doc.core_properties.pages or 1
    except Exception:
        logger.exception("[plan_limits] Failed to read page count from uploaded file")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not read the uploaded document. Please ensure it is a valid DOCX or PDF file.",
        )

    logger.info(
        "[plan_limits] uid=%s plan=%s pages=%d max_pages=%d",
        uid, plan, pages, max_pages,
    )

    if pages > max_pages:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Your document has {pages} pages, which exceeds the {max_pages}-page limit "
                f"for the {plan} plan. Please upgrade to Premium to process larger documents."
            ),
        )

    return {"plan": plan, "pages": pages}


async def check_reference_files_page_limit(
    files: List[UploadFile] = File(default=[]),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    """
    FastAPI dependency that counts the pages in all uploaded reference files combined
    and enforces the plan's max_reference_pages limit.
    """
    if not files:
        return {"plan": _resolve_active_plan(current_user.uid), "pages": 0}

    uid = current_user.uid
    plan = _resolve_active_plan(uid)
    constraints = get_plan_constraints(plan)
    max_reference_pages = constraints.get("max_reference_pages", 5)

    total_pages = 0

    for file in files:
        if not file.filename:
            continue
            
        file_bytes = await file.read()
        await file.seek(0)
        
        filename = file.filename or ""
        try:
            if filename.lower().endswith(".pdf"):
                import fitz
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                total_pages += doc.page_count
            elif filename.lower().endswith(".docx"):
                doc = Document(BytesIO(file_bytes))
                total_pages += doc.core_properties.pages or 1
        except Exception:
            logger.exception("[plan_limits] Failed to read page count from reference file: %s", filename)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not read the uploaded reference file: {filename}. Please ensure it is a valid DOCX or PDF.",
            )

    logger.info(
        "[plan_limits] uid=%s plan=%s total_reference_pages=%d max_reference_pages=%d",
        uid, plan, total_pages, max_reference_pages,
    )

    if total_pages > max_reference_pages:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Your reference documents total {total_pages} pages, which exceeds the {max_reference_pages}-page limit "
                f"for the {plan} plan. Please upgrade to Premium to upload larger reference files."
            ),
        )

    return {"plan": plan, "pages": total_pages}
