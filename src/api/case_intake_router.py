# src/api/case_intake_router.py

import uuid
import logging
import asyncio
import json
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, File, UploadFile, Form
from pydantic import BaseModel

from src.auth.firebase_auth import CurrentUser, get_current_user

from src.orchestrators.document_orchestrator import (
    document_orchestrator,
)

from src.agents.case_intake_agent.schema.global_state import (
    AgentState,
)
from src.queues.intake_queue import enqueue_intake_job
from src.utils.cleanup import cleanup_temp_file

router = APIRouter(prefix="/agents/intake", tags=["case-intake-agent"])

# In-process fallback job store (used when Redis is unavailable)
JOBS: Dict[str, Dict[str, Any]] = {}


class IntakeRequest(BaseModel):
    session_id: str
    template_id: str
    uploaded_files: Optional[List[str]] = []
    user_message: Optional[str] = ""
    chat_history: Optional[List[Dict[str, Any]]] = []


@router.post("/", status_code=202)
def start_intake(
    background_tasks: BackgroundTasks,
    session_id: str = Form(...),
    template_id: str = Form(...),
    user_message: Optional[str] = Form(""),
    chat_history: Optional[str] = Form("[]"),
    files: Optional[List[UploadFile]] = File(None),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Trigger a Case Intake Agent run.

    - If Redis is available: enqueues the job to the "intake" RQ queue.
    - Otherwise: runs the job in a FastAPI background task (single-process fallback).
    """
    try:
        chat_history_parsed = json.loads(chat_history) if chat_history else []
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid chat_history JSON: {e}")

    uploaded_files = []
    if files:
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        for file in files:
            if not file.filename:
                continue
            temp_file_path = temp_dir / file.filename
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            uploaded_files.append(str(temp_file_path.absolute()))

    payload = {
        "session_id": session_id,
        "template_id": template_id,
        "user_message": user_message,
        "chat_history": chat_history_parsed,
        "uploaded_files": uploaded_files,
        "uid": current_user.uid
    }

    # Try Redis RQ first
    job_id = enqueue_intake_job(payload)
    if job_id:
        return {"job_id": job_id, "status": "queued", "backend": "rq"}

    # Fallback: in-process background task
    job_id = uuid.uuid4().hex
    JOBS[job_id] = {"status": "queued", "result": None, "error": None}
    background_tasks.add_task(_run_intake_inproc, job_id, payload)
    return {"job_id": job_id, "status": "queued", "backend": "inproc"}


def _run_intake_inproc(job_id: str, payload: Dict[str, Any]):
    logging.info("Starting intake job (inproc) %s", job_id)
    JOBS[job_id]["status"] = "running"
    uploaded_files = payload.get("uploaded_files", [])
    try:
        initial_state: AgentState = {
            "session_id": payload.get("session_id", ""),
            "template_id": payload.get("template_id", ""),
            "field_manifest": {},
            "missing_fields": [],
            "case_data": {},
            "extracted_evidence": [],
            "uploaded_files": uploaded_files,
            "completion_percentage": 0.0,
            "ready_to_generate": False,
            "user_message": payload.get("user_message", ""),
            "chat_history": payload.get("chat_history", []),
            "error": None,
            "next_question": None,
        }
        # case_intake_graph uses async nodes — run via asyncio
        result = asyncio.run(
            document_orchestrator.run(
                initial_state
            )
        )
        JOBS[job_id]["status"] = "completed"
        JOBS[job_id]["result"] = result
    except Exception as e:
        logging.exception("Intake inproc job failed %s", job_id)
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["error"] = str(e)
    finally:
        for file_path in uploaded_files:
            cleanup_temp_file(file_path)


@router.get("/status/{job_id}")
def get_status(job_id: str):
    """Poll in-process job status (only relevant when Redis is unavailable)."""
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="job not found")
    return JOBS[job_id]
