# src/api/setup_router.py

import uuid
import logging
from typing import Optional, Dict, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from src.auth.firebase_auth import CurrentUser, get_current_user

from src.agents.setup_agent.graph import setup_agent_graph
from src.agents.setup_agent.schema.global_state import AgentState
from src.queues.setup_queue import enqueue_setup_job

from src.utils.create_template_registry_entry import (
    create_template_registry_entry,
)

router = APIRouter(
    prefix="/agents/setup",
    tags=["setup-agent"],
)

# In-process fallback job store (used when Redis is unavailable)
JOBS: Dict[str, Dict[str, Any]] = {}


class SetupRequest(BaseModel):
    file_path: str
    vault_name: str
    template_name: str
    template_id: Optional[str] = ""


@router.post("/", status_code=202)
def start_setup(
    req: SetupRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Trigger a Setup Agent run.

    - If Redis is available: enqueues the job to the "setup" RQ queue.
    - Otherwise: runs the job in a FastAPI background task (single-process fallback).
    """

    payload = req.dict()
    # Inject the verified uid as lawyer_id so downstream agents and Firestore
    # entries are keyed to the authenticated user — not a client-supplied value.
    payload["lawyer_id"] = current_user.uid

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

    try:

        template_id = (
            payload.get("template_id")
            or str(uuid.uuid4())
        )

        create_template_registry_entry(
            template_id=template_id,
            lawyer_id=payload["lawyer_id"],
            vault_name=payload["vault_name"],
            template_name=payload["template_name"],
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


@router.get("/status/{job_id}")
def get_status(
    job_id: str,
):
    """
    Poll in-process job status
    (only relevant when Redis is unavailable).
    """

    if job_id not in JOBS:

        raise HTTPException(
            status_code=404,
            detail="job not found",
        )

    return JOBS[job_id]