# src/core/firebase.py

import json
from pathlib import Path
from typing import Any

from src.core.config import settings

# Try importing firebase_admin; if unavailable, use a lightweight local mock when
# running in local/test mode so code doesn't crash at import time.
try:
    import firebase_admin
    from firebase_admin import credentials, firestore, storage
    _HAS_FIREBASE = True
except Exception:
    firebase_admin = None
    credentials = None
    firestore = None
    storage = None
    _HAS_FIREBASE = False


def initialize_firebase():
    """Initialize Firebase application once. Returns the firebase app or None.

    When `firebase_admin` is not installed and `settings.allow_firebase_mocks` is
    True (or `settings.LOCAL_TEST`), this returns None and the module will use
    a local mock Firestore.
    """
    if not _HAS_FIREBASE:
        return None

    if firebase_admin._apps:
        return firebase_admin.get_app()

    if settings.firebase_credentials_path:
        cred = credentials.Certificate(settings.firebase_credentials_path)
    else:
        # Fallback to Application Default Credentials on Cloud Run / GCP environments
        try:
            cred = credentials.ApplicationDefault()
        except Exception as e:
            # If not in GCP and no credentials path, we might want to fall back to mocks
            if settings.allow_firebase_mocks or settings.LOCAL_TEST:
                return None
            raise e

    # Build options
    options = {}
    proj_id = settings.firebase_project_id or settings.project_id
    if proj_id:
        options["projectId"] = proj_id
        
    bucket_name = settings.firebase_storage_bucket
    if not bucket_name and proj_id:
        bucket_name = f"{proj_id}.firebasestorage.app"
    if bucket_name:
        options["storageBucket"] = bucket_name

    return firebase_admin.initialize_app(cred, options)


class _MockDocument:
    def __init__(self, path: Path):
        self.path = path

    def set(self, data: Any):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def update(self, data: dict):
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        else:
            existing = {}
        existing.update(data)
        self.set(existing)


class _MockCollection:
    def __init__(self, name: str, base_dir: Path):
        self.name = name
        self.base_dir = base_dir

    def document(self, doc_id: str):
        path = self.base_dir / self.name / f"{doc_id}.json"
        return _MockDocument(path)


class _MockDB:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def collection(self, name: str):
        return _MockCollection(name, self.base_dir)


def get_firestore():
    """Return a Firestore client or a local mock when running locally.

    The mock stores documents as JSON under `.local_firestore/<collection>/<id>.json`.
    """
    if _HAS_FIREBASE:
        if settings.firebase_credentials_path or not (settings.allow_firebase_mocks or settings.LOCAL_TEST):
            initialize_firebase()
            return firestore.client()

    # Not installed or credentials missing: return a simple local mock when allowed
    if settings.allow_firebase_mocks or settings.LOCAL_TEST:
        base = Path(".local_firestore")
        base.mkdir(exist_ok=True)
        return _MockDB(base)

    raise ImportError(
        "firebase_admin is not installed or credentials not set, and local mocks are disabled."
    )


def get_storage():
    """Return Firebase Storage bucket or None when running locally without firebase.

    The mock is not implemented fully; callers should guard for None when running
    in local/test mode.
    """
    if _HAS_FIREBASE:
        if settings.firebase_credentials_path or not (settings.allow_firebase_mocks or settings.LOCAL_TEST):
            initialize_firebase()
            return storage.bucket()

    if settings.allow_firebase_mocks or settings.LOCAL_TEST:
        return None

    raise ImportError(
        "firebase_admin is not installed or credentials not set, and local mocks are disabled."
    )


# Lazy-initialized globals (avoid heavy work at import time)
db = None
bucket = None

def ensure_globals():
    global db, bucket
    if db is None:
        db = get_firestore()
    if bucket is None:
        bucket = get_storage()