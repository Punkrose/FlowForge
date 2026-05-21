"""
TaskProgress - Persistent JSON-based progress tracking for automation tasks.

Saves step completion state to disk so tasks can be resumed after
interruptions or inspected for status at any time.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from flowforge.models.task import TaskResult, TaskStep, TaskStatus, StepStatus

logger = logging.getLogger(__name__)

DEFAULT_PROGRESS_DIR = Path.home() / ".flowforge" / "progress"


class TaskProgress:
    """Manage persistent progress for a running or completed task.

    Progress is saved as a JSON file on disk so that:
    - External tools can inspect task status.
    - Tasks can be resumed after a crash (by re-running uncompleted steps).
    - A human-readable summary is always available.

    Parameters
    ----------
    task_result : TaskResult
        The task result model to track.
    progress_dir : Path, optional
        Directory where progress JSON files are stored.  Defaults to
        ``~/.flowforge/progress/``.
    """

    def __init__(
        self,
        task_result: TaskResult,
        progress_dir: Optional[Path] = None,
    ) -> None:
        self._result = task_result
        self._dir = progress_dir or DEFAULT_PROGRESS_DIR
        self._dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def task_id(self) -> str:
        return self._result.task_id

    @property
    def file_path(self) -> Path:
        """Return the path to the on-disk progress JSON file."""
        return self._dir / f"{self.task_id}.json"

    # ------------------------------------------------------------------
    # Step management
    # ------------------------------------------------------------------

    def add_step(self, step: TaskStep) -> None:
        """Register a new step in the progress tracker."""
        self._result.steps.append(step)
        self._save()

    def complete_step(
        self,
        step_number: int,
        result_text: Optional[str] = None,
        screenshot_path: Optional[str] = None,
    ) -> None:
        """Mark the step at *step_number* as completed.

        Parameters
        ----------
        step_number : int
            Zero-indexed step position.
        result_text : str, optional
            Output or result text from the step.
        screenshot_path : str, optional
            Path to a screenshot captured after the step.
        """
        step = self._find_step(step_number)
        now = datetime.now(timezone.utc)
        step.status = StepStatus.COMPLETED
        step.result = result_text
        step.completed_at = now
        step.screenshot_path = screenshot_path
        if step.started_at:
            step.duration_ms = (now - step.started_at).total_seconds() * 1000
        self._result.steps_completed += 1
        if screenshot_path:
            self._result.screenshots.append(screenshot_path)
        self._save()

    def fail_step(self, step_number: int, error: str) -> None:
        """Mark a step as failed with an error message."""
        step = self._find_step(step_number)
        now = datetime.now(timezone.utc)
        step.status = StepStatus.FAILED
        step.error = error
        step.completed_at = now
        if step.started_at:
            step.duration_ms = (now - step.started_at).total_seconds() * 1000
        self._result.steps_failed += 1
        self._save()

    def start_step(self, step_number: int) -> None:
        """Mark a step as currently running."""
        step = self._find_step(step_number)
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now(timezone.utc)
        self._save()

    def is_step_done(self, step_number: int) -> bool:
        """Return True if the step at *step_number* has completed."""
        step = self._find_step(step_number, safe=True)
        return step is not None and step.status == StepStatus.COMPLETED

    def get_pending_steps(self) -> list[TaskStep]:
        """Return all steps that have not yet been executed."""
        return [s for s in self._result.steps if s.status == StepStatus.PENDING]

    # ------------------------------------------------------------------
    # Task-level helpers
    # ------------------------------------------------------------------

    def set_status(self, status: TaskStatus) -> None:
        """Update overall task status and persist."""
        self._result.status = status
        self._save()

    def set_summary(self, summary: str) -> None:
        """Attach an LLM-generated summary to the task."""
        self._result.summary = summary
        self._save()

    def mark_completed(self) -> None:
        """Mark the entire task as successfully completed."""
        self._result.status = TaskStatus.COMPLETED
        self._result.completed_at = datetime.now(timezone.utc)
        if self._result.started_at:
            self._result.total_duration_ms = (
                self._result.completed_at - self._result.started_at
            ).total_seconds() * 1000
        self._save()

    def mark_failed(self, error: str) -> None:
        """Mark the entire task as failed."""
        self._result.status = TaskStatus.FAILED
        self._result.error = error
        self._result.completed_at = datetime.now(timezone.utc)
        if self._result.started_at:
            self._result.total_duration_ms = (
                self._result.completed_at - self._result.started_at
            ).total_seconds() * 1000
        self._save()

    def summary(self) -> dict[str, Any]:
        """Return a compact summary dictionary suitable for logging or display."""
        return {
            "task_id": self.task_id,
            "status": self._result.status.value,
            "steps_total": len(self._result.steps),
            "steps_completed": self._result.steps_completed,
            "steps_failed": self._result.steps_failed,
            "progress_percent": self._result.progress_percent,
            "error": self._result.error,
        }

    @property
    def result(self) -> TaskResult:
        """Return the underlying TaskResult model."""
        return self._result

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save(self) -> None:
        """Serialize current progress to disk."""
        try:
            self.file_path.write_text(
                self._result.model_dump_json(indent=2),
                encoding="utf-8",
            )
        except OSError:
            logger.exception("Failed to save progress for task %s", self.task_id)

    @classmethod
    def load(cls, task_id: str, progress_dir: Optional[Path] = None) -> Optional["TaskProgress"]:
        """Load a previously saved task progress from disk.

        Returns None if no progress file exists for the given task ID.
        """
        directory = progress_dir or DEFAULT_PROGRESS_DIR
        path = directory / f"{task_id}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            result = TaskResult.model_validate(data)
            return cls(result, progress_dir=directory)
        except (json.JSONDecodeError, Exception):
            logger.exception("Failed to load progress for task %s", task_id)
            return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_step(self, step_number: int, safe: bool = False) -> Optional[TaskStep]:
        """Find the step with the given step_number."""
        for step in self._result.steps:
            if step.step_number == step_number:
                return step
        if safe:
            return None
        raise IndexError(f"No step found with step_number={step_number}")
