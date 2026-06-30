# src/api/document_edit_router.py

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

from src.agents.document_edit_agent.graph import graph as document_edit_graph
from src.utils.cleanup import cleanup_temp_file
from src.queues.document_edit_queue import enqueue_document_edit_job

import os
from src.agents.document_edit_agent.helpers.redis_store import (
    save_job_result,
    get_job_result,
)

router = APIRouter(
    prefix="/agents/document-edit",
    tags=["document-edit-agent"],
)

# In-process fallback job store (used when Redis is unavailable)
JOBS: Dict[str, Dict[str, Any]] = {}


class DocumentEditRequest(BaseModel):
    template_id: str
    user_message: str
    messages: Optional[List[Dict[str, Any]]] = []


@router.post("/", status_code=202)
async def start_document_edit(
    background_tasks: BackgroundTasks,
    template_id: str = Form(...),
    user_message: str = Form(...),
    messages: Optional[str] = Form("[]"),
    files: Optional[List[UploadFile]] = File(None),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Trigger a Document Edit Agent run.

    - If Redis is available: enqueues the job to the "document_edit" RQ queue.
    - Otherwise: runs the job in a FastAPI background task (single-process fallback).
    """
    try:
        messages_parsed = json.loads(messages) if messages else []
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid messages JSON: {e}")

    uploaded_files = []
    if files:
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        for file in files:
            if not file.filename:
                continue

            filename = file.filename
            # Validate file type (must be pdf or docx)
            if not (filename.lower().endswith(".pdf") or filename.lower().endswith(".docx")):
                raise HTTPException(
                    status_code=400,
                    detail="Only PDF and DOCX files are supported."
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

            file_bytes = await file.read()
            gcs_path = f"uploads/document_edit/{current_user.uid}/{template_id}/{filename}"
            try:
                from src.core import firebase
                firebase.ensure_globals()
                bucket = firebase.bucket
                if bucket is None:
                    raise RuntimeError("Firebase Storage bucket is not initialized.")
                blob = bucket.blob(gcs_path)
                blob.upload_from_string(
                    file_bytes,
                    content_type=file.content_type or "application/octet-stream"
                )
                gcs_uri = f"gs://{bucket.name}/{gcs_path}"
                uploaded_files.append(gcs_uri)
                logging.info("Uploaded document edit file to Firebase Storage: %s", gcs_uri)
            except Exception as e:
                logging.exception("Failed to upload file to Firebase Storage")
                raise HTTPException(status_code=500, detail=f"Failed to upload file to storage: {e}")

    payload = {
        "template_id": template_id,
        "user_message": user_message,
        "messages": messages_parsed,
        "uploaded_files": uploaded_files,
        "lawyer_id": current_user.uid
    }

    # Try Redis RQ first
    job_id = enqueue_document_edit_job(
        payload,
    )

    if job_id:
        # Seed running status in Redis for early polling
        save_job_result(job_id, "running")
        return {
            "job_id": job_id,
            "status": "queued",
            "backend": "rq",
        }

    # Fallback: in-process background task
    job_id = uuid.uuid4().hex

    JOBS[job_id] = {
        "status": "queued",
        "generated_docxjs_code": "",
        "error": None,
    }
    save_job_result(job_id, "queued")

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
        "Starting document edit job (inproc) %s",
        job_id,
    )

    JOBS[job_id]["status"] = "running"
    save_job_result(job_id, "running")

    try:
        res = asyncio.run(_run_graph_async_inproc(payload))
        status = "failed" if res.get("error") else "completed"
        JOBS[job_id]["status"] = status
        JOBS[job_id]["generated_docxjs_code"] = res["generated_docxjs_code"]
        JOBS[job_id]["error"] = res["error"]
        
        save_job_result(job_id, status, res["generated_docxjs_code"], res["error"])
    except Exception as e:
        logging.exception(
            "Document edit inproc job failed %s",
            job_id,
        )
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["error"] = str(e)
        save_job_result(job_id, "failed", "", str(e))


async def _run_graph_async_inproc(payload: Dict[str, Any]) -> Dict[str, Any]:
    initial_state = {
        "lawyer_id": payload.get("lawyer_id", ""),
        "template_id": payload.get("template_id", ""),
        "user_message": payload.get("user_message", ""),
        "temp_file_path": "",
        "document_config": {},
        "blueprint": {},
        "messages": payload.get("messages", []),
        "uploaded_files": payload.get("uploaded_files", []),
        "error": None,
    }

    temp_file_path = None
    generated_code = ""
    result = None
    try:
        result = await document_edit_graph.ainvoke(initial_state)
        if result:
            if "temp_file_path" in result:
                temp_file_path = result["temp_file_path"]
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        with open(temp_file_path, "r", encoding="utf-8") as f:
                            generated_code = f.read()
                    except Exception:
                        logging.exception("Failed to read temporary file")
        return {
            "result_state": result,
            "generated_docxjs_code": generated_code,
            "error": result.get("error") if result else None
        }
    finally:
        cleanup_temp_file(temp_file_path)
        for f_path in payload.get("uploaded_files", []):
            cleanup_temp_file(f_path)


@router.get("/status/{job_id}")
async def get_status(
    job_id: str,
):
    """
    Poll job status and results from Redis, falling back to in-process memory.
    """
    # 1. Try reading from Redis first
    result = get_job_result(job_id)
    if result:
        if result["status"] in ("running", "queued"):
            return {"status": result["status"]}
        return {
            "status": result["status"],
            "generated_docxjs_code": result["generated_docxjs_code"],
            "error": result.get("error")
        }

    # 2. Fallback: Check local JOBS memory store
    if job_id not in JOBS:
        raise HTTPException(
            status_code=404,
            detail="job not found",
        )

    job = JOBS[job_id]
    if job["status"] in ("running", "queued"):
        return {"status": job["status"]}

    return {
        "status": job["status"],
        "generated_docxjs_code": job["generated_docxjs_code"],
        "error": job["error"]
    }



