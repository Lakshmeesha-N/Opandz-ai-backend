from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.setup_router import (
    router as setup_router,
)

from src.api.case_intake_router import (
    router as case_intake_router,
)

from src.api.document_edit_router import (
    router as document_edit_router,
)

from src.api.generated_document_router import (
    router as generated_document_router,
)

from src.api.template_registry_router import (
    router as template_registry_router,
)

from src.api.auth_router import (
    router as auth_router,
)

from src.api.middleware.usage_limit_middleware import UsageLimitMiddleware


app = FastAPI(
    title="Opandz AI Backend",
    version="1.0.0",
)

# ── Middleware (registered in reverse order — last added = outermost) ──────
# UsageLimitMiddleware: enforces 4-hour rolling token budget per user
app.add_middleware(UsageLimitMiddleware)

# CORSMiddleware: must be outermost so it handles preflight OPTIONS requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://opandzai.web.app",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=[
        "*",
    ],
    allow_headers=[
        "*",
    ],
)



@app.get(
    "/",
)
async def root():

    return {
        "message": "Opandz AI Backend",
    }


@app.get(
    "/health",
)
async def health():

    return {
        "status": "ok",
    }


app.include_router(
    setup_router,
)

app.include_router(
    case_intake_router,
)

app.include_router(
    document_edit_router,
)

app.include_router(
    generated_document_router,
)

app.include_router(
    template_registry_router,
)

app.include_router(
    auth_router,
)