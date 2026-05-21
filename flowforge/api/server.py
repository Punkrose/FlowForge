"""
FlowForge API Server - FastAPI application for remote task execution.

Provides REST endpoints for:
- Creating and monitoring automation tasks.
- Managing browser profiles.
- Health checks.

Run with:  uvicorn flowforge.api.server:app --host 0.0.0.0 --port 8080
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from flowforge.engine.automator import FlowForge
from flowforge.engine.profile_manager import ProfileManager
from flowforge.models.task import (
    ProfileCreate,
    ProfileInfo,
    TaskCreate,
    TaskResult,
    TaskStatus,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="FlowForge API",
    description=(
        "AI-powered browser automation API.  Send a natural language task "
        "description and FlowForge will plan and execute browser steps to "
        "accomplish it."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — wide open for development; tighten in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Shared state
# ---------------------------------------------------------------------------

# In-memory task store.  For production, replace with Redis / a database.
_tasks: dict[str, TaskResult] = {}

# Background task handles so we can cancel if needed.
_running_tasks: dict[str, asyncio.Task] = {}

_profile_mgr = ProfileManager()


def _get_engine() -> FlowForge:
    """Create a FlowForge engine instance from environment or defaults.

    In a real deployment you'd read API keys from env vars or a config file.
    """
    import os

    api_key = os.environ.get("FLOWFORGE_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
    base_url = os.environ.get("FLOWFORGE_BASE_URL", "https://api.openai.com/v1")
    model = os.environ.get("FLOWFORGE_MODEL", "gpt-4o")

    if not api_key:
        raise RuntimeError(
            "No LLM API key configured. Set FLOWFORGE_API_KEY or OPENAI_API_KEY."
        )

    return FlowForge(api_key=api_key, base_url=base_url, model=model)


# ---------------------------------------------------------------------------
# Routes: Health
# ---------------------------------------------------------------------------


@app.get("/api/health", tags=["Health"])
async def health_check() -> dict[str, Any]:
    """Return service health and basic stats."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "tasks_tracked": len(_tasks),
        "tasks_running": len(_running_tasks),
    }


# ---------------------------------------------------------------------------
# Routes: Tasks
# ---------------------------------------------------------------------------


@app.post("/api/tasks", response_model=TaskResult, status_code=202, tags=["Tasks"])
async def create_task(body: TaskCreate) -> TaskResult:
    """Create and start a new automation task.

    The task begins executing in the background.  Poll
    ``GET /api/tasks/{task_id}`` for status updates.
    """
    task_id = str(uuid.uuid4())
    initial = TaskResult(
        task_id=task_id,
        task_description=body.task,
        status=TaskStatus.PENDING,
        profile_used=body.profile,
    )
    _tasks[task_id] = initial

    # Fire-and-forget background execution
    bg = asyncio.create_task(_run_task(task_id, body))
    _running_tasks[task_id] = bg

    return initial


async def _run_task(task_id: str, body: TaskCreate) -> None:
    """Background coroutine that executes the task."""
    try:
        engine = _get_engine()
        result = await engine.run(
            task_description=body.task,
            profile=body.profile,
            headless=body.headless,
            max_steps=body.max_steps,
            timeout_seconds=body.timeout_seconds,
            extra_context=body.extra_context,
        )
        _tasks[task_id] = result
    except Exception as exc:
        logger.exception("Background task %s failed", task_id)
        if task_id in _tasks:
            _tasks[task_id].status = TaskStatus.FAILED
            _tasks[task_id].error = str(exc)
    finally:
        _running_tasks.pop(task_id, None)


@app.get("/api/tasks", response_model=list[TaskResult], tags=["Tasks"])
async def list_tasks() -> list[TaskResult]:
    """List all tracked tasks with their current status."""
    return list(_tasks.values())


@app.get("/api/tasks/{task_id}", response_model=TaskResult, tags=["Tasks"])
async def get_task(task_id: str) -> TaskResult:
    """Get the status and result of a specific task."""
    task = _tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    return task


@app.delete("/api/tasks/{task_id}", status_code=204, tags=["Tasks"])
async def cancel_task(task_id: str) -> None:
    """Cancel a running task."""
    bg = _running_tasks.get(task_id)
    if bg and not bg.done():
        bg.cancel()
        if task_id in _tasks:
            _tasks[task_id].status = TaskStatus.CANCELLED
    elif task_id not in _tasks:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")


# ---------------------------------------------------------------------------
# Routes: Profiles
# ---------------------------------------------------------------------------


@app.get("/api/profiles", response_model=list[ProfileInfo], tags=["Profiles"])
async def list_profiles() -> list[ProfileInfo]:
    """List all browser profiles."""
    return _profile_mgr.list_profiles()


@app.post("/api/profiles", response_model=ProfileInfo, status_code=201, tags=["Profiles"])
async def create_profile(body: ProfileCreate) -> ProfileInfo:
    """Create a new browser profile."""
    try:
        return _profile_mgr.create_profile(body.name, description=body.description)
    except FileExistsError:
        raise HTTPException(
            status_code=409, detail=f"Profile '{body.name}' already exists"
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.delete("/api/profiles/{name}", status_code=204, tags=["Profiles"])
async def delete_profile(name: str) -> None:
    """Delete a browser profile."""
    if not _profile_mgr.delete_profile(name):
        raise HTTPException(
            status_code=404,
            detail=f"Profile '{name}' not found or is locked",
        )


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the server directly (``python -m flowforge.api.server``)."""
    import uvicorn

    uvicorn.run(
        "flowforge.api.server:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
