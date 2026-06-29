# src/api/auth_router.py
"""
Authentication router.

POST /auth/me
  - Validates the Firebase ID token via get_current_user dependency.
  - Creates the user document in Firestore (users/{uid}) on first login.
  - Returns the user profile on subsequent calls.
"""

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from src.auth.firebase_auth import CurrentUser, get_current_user
from src.core.firebase import get_db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


def _get_or_create_user(uid: str, email: str | None, display_name: str | None) -> dict:
    """
    Firestore read/write for users/{uid}.  Runs synchronously; called via
    asyncio.to_thread so the async endpoint is not blocked.

    - New users are created with ``plan="free"``.
    - Existing users that pre-date the plan field are silently backfilled to
      ``plan="free"`` so every profile always has the field present.
    """
    db = get_db()
    user_ref = db.collection("users").document(uid)
    doc = user_ref.get()

    now = datetime.now(timezone.utc)

    if doc.exists:
        data = doc.to_dict()
        # Backfill: if an older profile is missing the plan field, set it now.
        if "plan" not in data:
            user_ref.update({"plan": "free", "updated_at": now})
            data["plan"] = "free"
        return data

    # First-time login: create the profile with plan="free".
    profile = {
        "uid": uid,
        "email": email,
        "display_name": display_name,
        "plan": "free",          # always starts on the free tier
        "created_at": now,
        "updated_at": now,
    }
    user_ref.set(profile)
    logger.info("Created new user profile for uid=%s (plan=free)", uid)
    return profile


@router.post(
    "/me",
    summary="Get or create the authenticated user profile",
    response_description="The authenticated user's Firestore profile",
)
async def get_or_create_me(
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Verify the caller's Firebase ID token, then:

    - If ``users/{uid}`` does **not** exist in Firestore → create it and return it.
    - If it already exists → return the existing profile unchanged.
    """
    try:
        profile = await asyncio.to_thread(
            _get_or_create_user,
            current_user.uid,
            current_user.email,
            current_user.display_name,
        )
    except Exception as exc:
        logger.exception("Failed to get/create user profile for uid=%s", current_user.uid)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve user profile.",
        ) from exc

    return profile
