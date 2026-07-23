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

    def set(self, data: Any, merge: bool = False, **kwargs):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        
        if merge and self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = {}
            if isinstance(existing, dict) and isinstance(data, dict):
                existing.update(data)
                data = existing

        def custom_serializer(obj):
            from datetime import datetime
            if isinstance(obj, datetime):
                return obj.isoformat()
            if hasattr(obj, "__class__") and "Sentinel" in getattr(obj, "__class__", {}).__name__:
                return datetime.now().isoformat()
            return str(obj)
            
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=custom_serializer)


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

    def add(self, data: dict):
        import uuid
        doc_id = str(uuid.uuid4())
        doc = self.document(doc_id)
        doc.set(data)
        return None, doc


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
    import logging as _logging
    if _HAS_FIREBASE:
        if settings.firebase_credentials_path or not (settings.allow_firebase_mocks or settings.LOCAL_TEST):
            initialize_firebase()
            bucket_name = settings.firebase_storage_bucket
            if not bucket_name:
                proj_id = settings.firebase_project_id or settings.project_id
                if proj_id:
                    bucket_name = f"{proj_id}.firebasestorage.app"
            if not bucket_name:
                _logging.warning(
                    "firebase.get_storage: FIREBASE_STORAGE_BUCKET is not set and "
                    "project_id is unknown — storage bucket unavailable."
                )
                return None
            return storage.bucket(bucket_name)

    if settings.allow_firebase_mocks or settings.LOCAL_TEST:
        return None

    raise ImportError(
        "firebase_admin is not installed or credentials not set, and local mocks are disabled."
    )


# Module-level globals — initialized immediately so that
# ``from src.core.firebase import db`` always yields a live client.
db = None
bucket = None


def ensure_globals():
    """Populate the module-level ``db`` and ``bucket`` singletons.

    Safe to call multiple times; subsequent calls are no-ops once the
    clients have been created.
    """
    global db, bucket
    if db is None:
        db = get_firestore()
    if bucket is None:
        bucket = get_storage()


def get_db():
    """Return the live Firestore client, initializing it if necessary.

    Prefer this over importing ``db`` directly because Python's module
    import caches the *value* at import time.  If ``db`` is still None
    when the importing module is first loaded (e.g. during unit tests or
    if the app starts before Firebase initializes), the cached reference
    stays None forever.  Calling ``get_db()`` always returns the current
    value after ensuring initialization has occurred.
    """
    ensure_globals()
    if db is None:
        raise RuntimeError(
            "Firestore client could not be initialized. "
            "Check Firebase credentials / environment configuration."
        )
    return db


def get_bucket():
    """Return the live Firebase Storage bucket, initializing it if necessary.

    Same rationale as ``get_db()``.  Returns None in local/test mode where
    storage is not available.
    """
    ensure_globals()
    return bucket


# Eager initialization removed to prevent import-time credential resolution.
# Callers must use get_db() or get_bucket() to ensure lazy initialization.
# ensure_globals()
