"""
Pydantic models for FlowForge tasks, results, and profiles.

These models define the data contracts used throughout the framework,
including API request/response schemas and internal data structures.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class StepStatus(str, Enum):
    """Status of an individual task step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskStatus(str, Enum):
    """Overall status of a task."""

    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BrowserAction(str, Enum):
    """Supported browser automation actions."""

    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    FILL = "fill"
    SELECT = "select"
    WAIT = "wait"
    WAIT_FOR_SELECTOR = "wait_for_selector"
    SCREENSHOT = "screenshot"
    EXTRACT_TEXT = "extract_text"
    SCROLL = "scroll"
    PRESS_KEY = "press_key"
    HOVER = "hover"
    UPLOAD_FILE = "upload_file"
    EVALUATE = "evaluate"
    OTP_FILL = "otp_fill"
    ASSERT_TEXT = "assert_text"
    ASSERT_VISIBLE = "assert_visible"


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------


class TaskCreate(BaseModel):
    """Request body for creating a new automation task."""

    task: str = Field(
        ...,
        description="Natural language description of the task to automate.",
        min_length=1,
        max_length=10000,
        examples=["Go to https://example.com/login, fill in the login form with username 'admin' and password 'secret123', then click the login button."],
    )
    profile: Optional[str] = Field(
        default=None,
        description="Browser profile name to use. Creates one if it doesn't exist.",
    )
    headless: bool = Field(
        default=True,
        description="Whether to run the browser in headless mode.",
    )
    max_steps: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of steps the planner can generate.",
    )
    timeout_seconds: int = Field(
        default=300,
        ge=30,
        le=3600,
        description="Maximum total execution time for the task.",
    )
    extra_context: Optional[str] = Field(
        default=None,
        description="Additional context or instructions for the planner.",
    )


class ProfileCreate(BaseModel):
    """Request body for creating a new browser profile."""

    name: str = Field(
        ...,
        description="Profile name (alphanumeric, hyphens, underscores).",
        min_length=1,
        max_length=64,
        pattern=r"^[a-zA-Z0-9_-]+$",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=256,
        description="Optional human-readable description.",
    )


# ---------------------------------------------------------------------------
# Response / Internal Models
# ---------------------------------------------------------------------------


class TaskStep(BaseModel):
    """A single step in an automation task plan."""

    id: int = Field(default_factory=lambda: uuid.uuid4().int % 1_000_000, description="Unique step identifier.")
    step_number: int = Field(..., ge=0, description="Zero-indexed position in the plan.")
    action: str = Field(..., description="The browser action to perform (e.g. navigate, click, type).")
    target: Optional[str] = Field(default=None, description="CSS selector, URL, or other target identifier.")
    value: Optional[str] = Field(default=None, description="Value to type, select, or use as parameter.")
    description: str = Field(..., description="Human-readable description of what this step does.")
    status: StepStatus = Field(default=StepStatus.PENDING, description="Current execution status.")
    result: Optional[str] = Field(default=None, description="Result or output from executing this step.")
    error: Optional[str] = Field(default=None, description="Error message if the step failed.")
    screenshot_path: Optional[str] = Field(default=None, description="Path to screenshot taken after this step.")
    started_at: Optional[datetime] = Field(default=None, description="When execution of this step began.")
    completed_at: Optional[datetime] = Field(default=None, description="When execution of this step finished.")
    duration_ms: Optional[float] = Field(default=None, description="Execution duration in milliseconds.")


class TaskResult(BaseModel):
    """Complete result of an automation task execution."""

    task_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique task identifier.",
    )
    task_description: str = Field(..., description="The original natural language task description.")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Overall task status.")
    steps: list[TaskStep] = Field(default_factory=list, description="Ordered list of planned/executed steps.")
    steps_completed: int = Field(default=0, description="Number of steps that completed successfully.")
    steps_failed: int = Field(default=0, description="Number of steps that failed.")
    summary: Optional[str] = Field(default=None, description="LLM-generated summary of the task execution.")
    error: Optional[str] = Field(default=None, description="Top-level error message if the task failed.")
    screenshots: list[str] = Field(default_factory=list, description="Paths to all screenshots collected during execution.")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the task was created.",
    )
    started_at: Optional[datetime] = Field(default=None, description="When task execution began.")
    completed_at: Optional[datetime] = Field(default=None, description="When task execution finished.")
    total_duration_ms: Optional[float] = Field(default=None, description="Total execution time in milliseconds.")
    profile_used: Optional[str] = Field(default=None, description="Browser profile used for this task.")

    @property
    def is_finished(self) -> bool:
        """Return True if the task has reached a terminal state."""
        return self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)

    @property
    def progress_percent(self) -> float:
        """Return completion percentage based on step counts."""
        total = len(self.steps)
        if total == 0:
            return 0.0
        return (self.steps_completed / total) * 100.0


class ProfileInfo(BaseModel):
    """Information about a browser profile."""

    name: str = Field(..., description="Profile name.")
    description: Optional[str] = Field(default=None, description="Human-readable description.")
    path: str = Field(..., description="Filesystem path to the profile data.")
    is_locked: bool = Field(default=False, description="Whether the profile is currently in use.")
    locked_by: Optional[str] = Field(default=None, description="Task ID that holds the lock.")
    created_at: Optional[datetime] = Field(default=None, description="When the profile was created.")
    last_used_at: Optional[datetime] = Field(default=None, description="When the profile was last used.")
