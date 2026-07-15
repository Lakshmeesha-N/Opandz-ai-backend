# src/auth/firebase_auth.py
"""
Firebase Authentication dependency for FastAPI.

Usage in a router:
    from src.auth.firebase_auth import get_current_user, CurrentUser
    from fastapi import Depends

    @router.post("/protected")
    async def protected(current_user: CurrentUser = Depends(get_current_user)):
        ...

Returns HTTP 401 for missing, malformed, expired, or invalid tokens.
"""

import logging
from typing import Any, Dict, Optional

import asyncio

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from src.core.firebase import initialize_firebase

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Try to import firebase_admin.auth.  When running locally without the SDK
# (or without credentials) the dependency will raise 503 rather than 401 to
# signal that auth is unavailable rather than forbidden.
# ---------------------------------------------------------------------------
try:
    from firebase_admin import auth as firebase_auth_module
    _HAS_AUTH = True
except ImportError:
    firebase_auth_module = None  # type: ignore[assignment]
    _HAS_AUTH = False


# HTTPBearer auto-extracts the Bearer token and returns 403 if the header is
# missing entirely. We override auto_error=False so we can return a clean 401.
_bearer_scheme = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

class CurrentUser(BaseModel):
    """Verified identity extracted from a Firebase ID token."""

    uid: str
    email: Optional[str] = None
    email_verified: bool = False
    display_name: Optional[str] = None
    custom_claims: Dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Token verification helper
# ---------------------------------------------------------------------------

def _verify_token_sync(token: str) -> Dict[str, Any]:
    """
    Verify a Firebase ID token synchronously.

    Raises:
        firebase_admin.auth.InvalidIdTokenError: on any token problem.
    """
    return firebase_auth_module.verify_id_token(token, check_revoked=True)


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

from fastapi import Request

async def get_current_user(request: Request) -> CurrentUser:
    """
    FastAPI dependency that returns the authenticated user.
    The actual Firebase token verification is now handled by UsageLimitMiddleware,
    which attaches the CurrentUser object to request.state.
    """
    user = getattr(request.state, "current_user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

