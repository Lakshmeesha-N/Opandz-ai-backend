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

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> CurrentUser:
    """
    FastAPI dependency that validates a Firebase Bearer token.

    - Extracts the token from ``Authorization: Bearer <token>``.
    - Verifies it against Firebase Auth (async-safe via thread executor).
    - Returns a :class:`CurrentUser` on success.
    - Raises HTTP 401 on any failure.
    """
    _unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # --- Guard: missing / malformed header ---
    if credentials is None or not credentials.credentials:
        raise _unauthorized

    # --- Guard: SDK not available (misconfigured environment) ---
    if not _HAS_AUTH or firebase_auth_module is None:
        logger.error(
            "firebase_admin is not installed; cannot verify token. "
            "Install it or set ALLOW_FIREBASE_MOCKS=true for local testing."
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is not configured.",
        )

    initialize_firebase()
    token = credentials.credentials

    try:
        # Run the blocking SDK call off the async event loop.
        loop = asyncio.get_event_loop()
        decoded = await loop.run_in_executor(None, _verify_token_sync, token)
    except Exception as exc:
        # Covers InvalidIdTokenError, ExpiredIdTokenError, RevokedIdTokenError,
        # CertificateFetchError, and any unexpected error.
        logger.warning("Token verification failed: %s", exc)
        raise _unauthorized from exc

    return CurrentUser(
        uid=decoded["uid"],
        email=decoded.get("email"),
        email_verified=decoded.get("email_verified", False),
        display_name=decoded.get("name"),
        custom_claims={
            k: v
            for k, v in decoded.items()
            if k not in {"uid", "email", "email_verified", "name", "iat", "exp", "aud", "iss", "sub"}
        },
    )
