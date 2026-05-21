"""
Tests for the TaskProgress class.
"""

import json
import tempfile
from pathlib import Path

import pytest

from flowforge.engine.progress import TaskProgress
from flowforge.models.task import TaskResult, TaskStep, TaskStatus, StepStatus


@pytest.fixture
def progress_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for progress files."""
    return tmp_path / "progress"


@pytest.fixture
def result() -> TaskResult:
    """Create a fresh TaskResult."""
    return TaskResult(task_id="test-001", task_description="Test task")


@pytest.fixture
def progress(result: TaskResult, progress_dir: Path) -> TaskProgress:
    """Create a TaskProgress instance with a temporary directory."""
    return TaskProgress(result, progress_dir=progress_dir)


class TestTaskProgress:
    """Unit tests for TaskProgress."""

    def test_file_path(self, progress: TaskProgress, progress_dir: Path) -> None:
        """file_path should point to the JSON file inside progress_dir."""
        expected = progress_dir / "test-001.json"
        assert progress.file_path == expected

    def test_add_step_persists(self, progress: TaskProgress) -> None:
        """Adding a step should save the progress to disk."""
        step = TaskStep(step_number=0, action="navigate", description="Go to example.com")
        progress.add_step(step)

        assert len(progress.result.steps) == 1
        assert progress.file_path.exists()

        # Verify JSON content
        data = json.loads(progress.file_path.read_text())
        assert len(data["steps"]) == 1
        assert data["steps"][0]["action"] == "navigate"

    def test_complete_step(self, progress: TaskProgress) -> None:
        """complete_step should update status and counters."""
        step = TaskStep(
            step_number=0,
            action="click",
            description="Click button",
            status=StepStatus.RUNNING,
        )
        progress.add_step(step)
        progress.start_step(0)
        progress.complete_step(0, result_text="clicked OK")

        assert progress.is_step_done(0)
        assert progress.result.steps_completed == 1
        assert progress.result.steps[0].result == "clicked OK"

    def test_fail_step(self, progress: TaskProgress) -> None:
        """fail_step should set error and increment failure count."""
        step = TaskStep(step_number=0, action="type", description="Type text")
        progress.add_step(step)
        progress.fail_step(0, "Element not found")

        assert progress.result.steps[0].status == StepStatus.FAILED
        assert progress.result.steps[0].error == "Element not found"
        assert progress.result.steps_failed == 1

    def test_is_step_done_returns_false_for_pending(self, progress: TaskProgress) -> None:
        """A pending step should not be reported as done."""
        step = TaskStep(step_number=0, action="wait", description="Wait 2s")
        progress.add_step(step)
        assert not progress.is_step_done(0)

    def test_is_step_done_returns_false_for_unknown(self, progress: TaskProgress) -> None:
        """A step_number with no matching step should return False (safe mode)."""
        assert not progress.is_step_done(999)

    def test_get_pending_steps(self, progress: TaskProgress) -> None:
        """Should return only steps not yet completed."""
        for i in range(3):
            progress.add_step(
                TaskStep(step_number=i, action="screenshot", description=f"Shot {i}")
            )
        progress.complete_step(1)

        pending = progress.get_pending_steps()
        assert len(pending) == 2
        assert all(s.status == StepStatus.PENDING for s in pending)

    def test_mark_completed(self, progress: TaskProgress) -> None:
        """mark_completed should set status and timestamps."""
        progress.mark_completed()
        assert progress.result.status == TaskStatus.COMPLETED
        assert progress.result.completed_at is not None

    def test_mark_failed(self, progress: TaskProgress) -> None:
        """mark_failed should set status and error."""
        progress.mark_failed("Timeout exceeded")
        assert progress.result.status == TaskStatus.FAILED
        assert progress.result.error == "Timeout exceeded"

    def test_summary(self, progress: TaskProgress) -> None:
        """summary() should return a dict with all expected keys."""
        progress.add_step(TaskStep(step_number=0, action="navigate", description="Go"))
        s = progress.summary()
        assert s["task_id"] == "test-001"
        assert s["steps_total"] == 1
        assert "status" in s
        assert "progress_percent" in s

    def test_load_roundtrip(self, progress: TaskProgress) -> None:
        """Save + load should reconstruct the same TaskResult."""
        progress.add_step(TaskStep(step_number=0, action="navigate", description="Go"))
        progress.complete_step(0, result_text="done")

        loaded = TaskProgress.load("test-001", progress_dir=progress.file_path.parent.parent)
        # Load from the same directory
        loaded = TaskProgress.load("test-001", progress_dir=progress._dir)
        assert loaded is not None
        assert loaded.task_id == "test-001"
        assert loaded.result.steps_completed == 1

    def test_load_nonexistent(self, progress_dir: Path) -> None:
        """Loading a nonexistent task should return None."""
        result = TaskProgress.load("no-such-task", progress_dir=progress_dir)
        assert result is None

    def test_set_summary(self, progress: TaskProgress) -> None:
        """set_summary should persist the summary text."""
        progress.set_summary("All steps completed successfully.")
        assert progress.result.summary == "All steps completed successfully."

        # Verify on disk
        data = json.loads(progress.file_path.read_text())
        assert data["summary"] == "All steps completed successfully."


class TestTaskResultModel:
    """Unit tests for TaskResult model properties."""

    def test_is_finished_completed(self) -> None:
        r = TaskResult(task_description="test", status=TaskStatus.COMPLETED)
        assert r.is_finished

    def test_is_finished_pending(self) -> None:
        r = TaskResult(task_description="test", status=TaskStatus.PENDING)
        assert not r.is_finished

    def test_progress_percent(self) -> None:
        r = TaskResult(task_description="test")
        r.steps = [
            TaskStep(step_number=0, action="a", description="d"),
            TaskStep(step_number=1, action="b", description="d"),
            TaskStep(step_number=2, action="c", description="d"),
        ]
        r.steps_completed = 2
        assert abs(r.progress_percent - 66.666) < 0.1

    def test_progress_percent_empty(self) -> None:
        r = TaskResult(task_description="test")
        assert r.progress_percent == 0.0
