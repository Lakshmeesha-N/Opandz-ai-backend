# src/api/template_registry_router.py

from fastapi import APIRouter, Depends, HTTPException

from src.auth.firebase_auth import CurrentUser, get_current_user
from src.core.firebase import get_db

router = APIRouter(
    prefix="/template-registry",
    tags=["template-registry"],
)


@router.get("/vaults")
def get_vaults(
    current_user: CurrentUser = Depends(get_current_user),
):
    """Return all vault names owned by the authenticated user."""

    from google.cloud.firestore import FieldFilter
    db = get_db()
    docs = (
        db.collection("template_registry")
        .where(filter=FieldFilter("lawyer_id", "==", current_user.uid))
        .stream()
    )

    vaults = set()

    for doc in docs:
        data = doc.to_dict()
        vaults.add(data["vault_name"])

    return {
        "uid": current_user.uid,
        "vaults": sorted(list(vaults)),
    }


@router.get("/vaults/{vault_name}")
def get_templates_in_vault(
    vault_name: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Return all templates inside a vault owned by the authenticated user."""

    from google.cloud.firestore import FieldFilter
    db = get_db()
    docs = (
        db.collection("template_registry")
        .where(filter=FieldFilter("lawyer_id", "==", current_user.uid))
        .where(filter=FieldFilter("vault_name", "==", vault_name))
        .stream()
    )

    templates = []

    for doc in docs:
        data = doc.to_dict()
        templates.append(
            {
                "template_id": data["template_id"],
                "template_name": data["template_name"],
                "pages": data.get("pages", 0),
            }
        )

    return {
        "uid": current_user.uid,
        "vault_name": vault_name,
        "templates": templates,
    }


@router.get("/templates/{template_id}")
def get_template(
    template_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Return a single template document.

    Returns 403 if the template belongs to a different user.
    """

    db = get_db()
    doc = (
        db.collection("template_registry")
        .document(template_id)
        .get()
    )

    if not doc.exists:
        raise HTTPException(
            status_code=404,
            detail="Template not found",
        )

    data = doc.to_dict()

    # Ownership check — the verified uid must match the stored lawyer_id.
    if data.get("lawyer_id") != current_user.uid:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this template.",
        )

    return data