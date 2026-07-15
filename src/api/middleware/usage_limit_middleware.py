# src/api/middleware/usage_limit_middleware.py
#
# FastAPI/Starlette middleware that enforces a 4-hour rolling token budget.
#
# This middleware only activates on agent API paths. Static/health routes are
# excluded so they are never blocked by a token-limit check.

import logging
from datetime import datetime, timedelta, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.core.subscription_config import get_plan_constraints, DEFAULT_PLAN

logger = logging.getLogger(__name__)

# Only enforce token limits on these URL prefixes.
# All other routes (/, /health, /auth/*) are excluded.
PROTECTED_PREFIXES = (
    "/agents/",
)

# URL prefixes that are always allowed through (e.g. preflight, health checks).
EXCLUDED_PREFIXES = (
    "/health",
    "/",
    "/auth/",
    "/docs",
    "/openapi",
    "/redoc",
)


def _is_protected(path: str) -> bool:
    """Return True if the request path requires authentication."""
    for prefix in EXCLUDED_PREFIXES:
        if path == prefix or path.startswith(prefix + "/"):
            return False
    return True


class UsageLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that handles Firebase token verification for all protected routes,
    and additionally blocks requests to /agents/ when a user has exceeded their
    4-hour rolling token budget.
    """

    async def dispatch(self, request: Request, call_next):

        if not _is_protected(request.url.path):
            return await call_next(request)

        # ── 1. Authenticate Token ───────────────────────────────────────────
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing authentication token."},
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header[len("Bearer "):]

        try:
            from src.core import firebase
            firebase.ensure_globals()
            from firebase_admin import auth as fb_auth
            decoded = fb_auth.verify_id_token(token)
            uid = decoded.get("uid")
            if not uid:
                raise ValueError("Token missing UID")
        except Exception as exc:
            logger.warning("[UsageLimitMiddleware] Token verification failed: %s", exc)
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired authentication token."},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Attach CurrentUser to request state for routers to use
        from src.auth.firebase_auth import CurrentUser
        request.state.current_user = CurrentUser(
            uid=uid,
            email=decoded.get("email"),
            email_verified=decoded.get("email_verified", False),
            display_name=decoded.get("name"),
            custom_claims={
                k: v
                for k, v in decoded.items()
                if k not in {"uid", "email", "email_verified", "name", "iat", "exp", "aud", "iss", "sub"}
            },
        )

        # ── 2. Usage Limit Check (only for /agents/ routes) ────────────────
        if request.url.path.startswith("/agents/"):
            try:
                from src.core.firebase import get_db
                db = get_db()
                user_ref = db.collection("users").document(uid)
                user_doc = user_ref.get()

                if user_doc.exists:
                    user_data = user_doc.to_dict()
                    plan = user_data.get("plan", DEFAULT_PLAN)
                    expires_at = user_data.get("expires_at")

                    # Auto-downgrade expired premium plans
                    if plan == "premium" and expires_at:
                        try:
                            expire_dt = (
                                expires_at
                                if isinstance(expires_at, datetime)
                                else expires_at.ToDatetime(tzinfo=timezone.utc)
                            )
                            if datetime.now(timezone.utc) > expire_dt:
                                plan = DEFAULT_PLAN
                                user_ref.update({"plan": DEFAULT_PLAN})
                                logger.info(
                                    "[UsageLimitMiddleware] Premium expired for uid=%s — downgraded to free",
                                    uid,
                                )
                        except Exception:
                            logger.exception(
                                "[UsageLimitMiddleware] Failed to check expiry for uid=%s", uid
                            )

                    # Check rolling 4-hour token budget
                    constraints = get_plan_constraints(plan)
                    max_tokens = constraints["max_tokens_4h"]
                    four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=4)

                    usage_docs = (
                        db.collection("token_usage")
                        .where("uid", "==", uid)
                        .where("timestamp", ">=", four_hours_ago)
                        .stream()
                    )
                    total_used = sum(
                        doc.to_dict().get("total_tokens", 0) for doc in usage_docs
                    )

                    logger.info(
                        "[UsageLimitMiddleware] uid=%s plan=%s tokens_4h=%d max=%d path=%s",
                        uid, plan, total_used, max_tokens, request.url.path,
                    )

                    if total_used >= max_tokens:
                        return JSONResponse(
                            status_code=429,
                            content={
                                "detail": (
                                    f"You have used {total_used:,} tokens in the last 4 hours, "
                                    f"reaching the {max_tokens:,}-token limit for the {plan} plan. "
                                    f"Please wait or upgrade to Premium."
                                )
                            },
                        )

            except Exception:
                # Never let middleware errors block legitimate requests
                logger.exception(
                    "[UsageLimitMiddleware] Unexpected error for uid=%s — allowing request through",
                    uid,
                )

        return await call_next(request)
