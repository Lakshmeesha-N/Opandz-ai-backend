
# src/api/setup_router.py

import uuid
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, File, UploadFile, Form
from pydantic import BaseModel

from src.auth.firebase_auth import CurrentUser, get_current_user

from src.agents.setup_agent.graph import setup_agent_graph
from src.agents.setup_agent.schema.global_state import AgentState
from src.queues.setup_queue import enqueue_setup_job

from src.utils.create_template_registry_entry import (
    create_template_registry_entry,
)
from src.utils.cleanup import cleanup_temp_file
from src.api.dependencies.plan_limits import (
    check_uploaded_file_page_limit,
)

router = APIRouter(
    prefix="/agents/setup",
    tags=["setup-agent"],
)

logger = logging.getLogger(__name__)

# In-process fallback job store (used when Redis is unavailable)
JOBS: Dict[str, Dict[str, Any]] = {}


@router.post("/", status_code=202)
async def start_setup(
    background_tasks: BackgroundTasks,
    vault_name: str = Form(...),
    template_name: str = Form(...),
    template_id: Optional[str] = Form(""),
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    plan_check: dict = Depends(check_uploaded_file_page_limit),
):
    """
    Trigger a Setup Agent run with an uploaded DOCX file.

    - Authenticates the user
    - Validates file type and size
    - If Redis is available: enqueues the job to the "setup" RQ queue.
    - Otherwise: runs the job in a FastAPI background task (single-process fallback).
    """
    filename = file.filename or ""
    # Validate file type (must be docx or pdf)
    if not filename.lower().endswith((".docx", ".pdf")):
        raise HTTPException(
            status_code=400,
            detail="Only DOCX and PDF files are supported for Blueprint Creation."
        )

    # Validate file size (must not exceed 1 MB)
    try:
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Failed to read the uploaded file size."
        )

    if file_size > 1 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="The selected document exceeds the maximum supported size (1 MB)."
        )

    # Upload file to Firebase Storage organized by user
    # Path: uploads/setup/{lawyer_id}/{template_id}/{filename}
    # Pages were already validated by the check_uploaded_file_page_limit dependency.
    # The dependency already called file.seek(0), so we can safely read here.
    pages = plan_check["pages"]

    file_bytes = await file.read()
    template_id_val = template_id or str(uuid.uuid4())
    gcs_path = f"uploads/setup/{current_user.uid}/{template_id_val}/{filename}"

    try:
        from src.core import firebase
        firebase.ensure_globals()
        bucket = firebase.bucket
        if bucket is None:
            raise RuntimeError("Firebase Storage bucket is not initialized.")
        blob = bucket.blob(gcs_path)
        blob.upload_from_string(
            file_bytes,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        gcs_uri = f"gs://{bucket.name}/{gcs_path}"
        logger.info("Uploaded file to Firebase Storage: %s", gcs_uri)
    except Exception as e:
        logger.exception("Failed to upload file to Firebase Storage")
        raise HTTPException(status_code=500, detail=f"Failed to upload file to storage: {e}")

    payload = {
        "file_path": gcs_uri,
        "vault_name": vault_name,
        "template_name": template_name,
        "template_id": template_id_val,
        "lawyer_id": current_user.uid,
        "pages": pages,
    }

    # Try Redis RQ first
    job_id = enqueue_setup_job(
        payload,
    )

    if job_id:
        return {
            "job_id": job_id,
            "status": "queued",
            "backend": "rq",
        }

    # Fallback: in-process background task
    job_id = uuid.uuid4().hex

    JOBS[job_id] = {
        "status": "queued",
        "result": None,
        "error": None,
    }

    background_tasks.add_task(
        _run_graph_inproc,
        job_id,
        payload,
    )

    return {
        "job_id": job_id,
        "status": "queued",
        "backend": "inproc",
    }


def _run_graph_inproc(
    job_id: str,
    payload: Dict[str, Any],
):

    logging.info(
        "Starting setup job (inproc) %s",
        job_id,
    )

    JOBS[job_id]["status"] = "running"

    from src.utils.token_context import set_token_context, reset_token_context
    uid_token, agent_token = set_token_context(payload.get("lawyer_id", ""), "setup")

    try:

        template_id = (
            payload.get("template_id")
            or str(uuid.uuid4())
        )

        initial_state: AgentState = {
            "file_path": payload["file_path"],
            "file_type": None,
            "docx_blueprint": None,
            "pdf_blueprint": None,
            "lawyer_id": payload["lawyer_id"],
            "template_id": template_id,
            "error": None,
        }

        result = setup_agent_graph.invoke(
            initial_state,
        )

        create_template_registry_entry(
            template_id=template_id,
            lawyer_id=payload["lawyer_id"],
            vault_name=payload["vault_name"],
            template_name=payload["template_name"],
            pages=payload.get("pages", 0),
        )

        JOBS[job_id]["status"] = "completed"
        JOBS[job_id]["result"] = result

    except Exception as e:

        logging.exception(
            "Setup inproc job failed %s",
            job_id,
        )

        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["error"] = str(
            e,
        )
    finally:
        cleanup_temp_file(payload.get("file_path"))
        reset_token_context(uid_token, agent_token)


@router.get("/status/{job_id}")
def get_status(
    job_id: str,
):
    """
    Poll job status.
    - For RQ-backed jobs: reads status from Firestore (written by the worker).
    - For in-process fallback jobs: reads from the in-memory JOBS dict.
    """
    # 1. Check Firestore first (RQ worker writes status here)
    try:
        from src.core import firebase
        firebase.ensure_globals()
        db = firebase.db
        if db:
            doc = db.collection("jobs").document(job_id).get()
            if doc.exists:
                return doc.to_dict()
    except Exception:
        logging.exception("Failed to read job status from Firestore for job %s", job_id)

    # 2. Check RQ/Redis directly (if the job is still queued or processing in Redis)
    try:
        from src.queues.redis_client import get_redis
        from rq.job import Job
        conn = get_redis()
        try:
            job = Job.fetch(job_id, connection=conn)
            status = job.get_status()
            if status == "finished":
                status = "completed"
            return {
                "job_id": job.id,
                "status": status,
                "backend": "rq"
            }
        except Exception:
            pass
    except Exception:
        logging.exception("Failed to read job status from Redis for job %s", job_id)

    # 3. Fallback: in-memory store (inproc background task path)
    if job_id in JOBS:
        return JOBS[job_id]

    raise HTTPException(
        status_code=404,
        detail="job not found",
    )