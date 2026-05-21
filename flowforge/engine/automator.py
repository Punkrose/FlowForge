"""
FlowForge Automator - Main orchestrator for AI-driven browser automation.

Takes a natural language task description, uses an OpenAI-compatible LLM to
generate a step-by-step plan, then executes each step against a live browser
session.  Supports any LLM provider that exposes an OpenAI-compatible API.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from flowforge.engine.session import BrowserSession
from flowforge.engine.otp_handler import OTPHandler
from flowforge.engine.profile_manager import ProfileManager
from flowforge.engine.progress import TaskProgress
from flowforge.models.task import (
    BrowserAction,
    StepStatus,
    TaskCreate,
    TaskResult,
    TaskStatus,
    TaskStep,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt sent to the LLM to produce a structured automation plan.
# ---------------------------------------------------------------------------

PLANNING_SYSTEM_PROMPT = """\
You are FlowForge, an expert browser automation planner. Given a natural language
task description, you produce a JSON array of browser automation steps.

Each step must be an object with these fields:
- "action": one of {actions}
- "target": CSS selector or URL (string or null)
- "value": text to type / select / evaluate (string or null)
- "description": human-readable explanation of what this step does

Rules:
1. The first step should almost always be a "navigate" to the target URL.
2. Use CSS selectors for targeting elements (e.g. "#login-btn", "input[name='email']").
3. If the user mentions filling an OTP, include an "otp_fill" step — the system
   will handle fetching the code from email automatically.
4. Include a "screenshot" step after critical actions for verification.
5. Keep the plan minimal but complete — every action the user requested must appear.
6. Use "wait_for_selector" after actions that trigger navigation or loading.
7. Return ONLY a valid JSON array — no markdown, no explanation.
""".format(
    actions=", ".join(a.value for a in BrowserAction)
)

SUMMARY_PROMPT = """\
Summarize the following browser automation task execution in 2-3 sentences.
Include what was attempted, whether it succeeded, and any notable observations.

Task: {task}
Steps executed:
{steps_json}
"""


class FlowForge:
    """AI-powered browser automation orchestrator.

    Uses an OpenAI-compatible LLM to convert natural language task descriptions
    into structured browser automation plans, then executes them step by step.

    Parameters
    ----------
    api_key : str
        API key for the LLM provider.
    base_url : str
        Base URL for the OpenAI-compatible API (e.g. ``https://api.openai.com/v1``).
    model : str
        Model identifier (e.g. ``gpt-4o``, ``claude-3-sonnet-20240229``).
    profile_dir : Path, optional
        Directory for browser profile storage.
    screenshots_dir : Path, optional
        Directory for saving screenshots.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o",
        profile_dir: Optional[Any] = None,
        screenshots_dir: Optional[Any] = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._http: Optional[httpx.AsyncClient] = None

        self._profile_mgr = ProfileManager(profile_dir)
        self._session: Optional[BrowserSession] = None
        self._otp: Optional[OTPHandler] = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def run(
        self,
        task_description: str,
        profile: Optional[str] = None,
        headless: bool = True,
        max_steps: int = 50,
        timeout_seconds: int = 300,
        extra_context: Optional[str] = None,
    ) -> TaskResult:
        """Plan and execute an automation task from a natural language description.

        This is the primary entry point. It:
        1. Creates a TaskResult and TaskProgress tracker.
        2. Calls the LLM to produce a step plan.
        3. Executes each step against a live browser.
        4. Generates an execution summary.

        Parameters
        ----------
        task_description : str
            What the browser should do, in plain English.
        profile : str, optional
            Browser profile name to use.
        headless : bool
            Whether to run headless.
        max_steps : int
            Maximum plan length.
        timeout_seconds : int
            Overall timeout.
        extra_context : str, optional
            Additional instructions for the planner.

        Returns
        -------
        TaskResult
            Full execution result with step details, screenshots, and summary.
        """
        task_id = str(uuid.uuid4())
        result = TaskResult(
            task_id=task_id,
            task_description=task_description,
            status=TaskStatus.PLANNING,
            profile_used=profile,
        )
        progress = TaskProgress(result)

        logger.info("Task %s: starting — %s", task_id, task_description[:120])

        try:
            # --- Planning phase ---
            plan = await self.plan(task_description, extra_context=extra_context)
            for i, step_data in enumerate(plan):
                step = TaskStep(
                    step_number=i,
                    action=step_data.get("action", "unknown"),
                    target=step_data.get("target"),
                    value=step_data.get("value"),
                    description=step_data.get("description", ""),
                )
                progress.add_step(step)

            if not plan:
                progress.mark_failed("LLM returned an empty plan.")
                return result

            logger.info("Task %s: plan has %d steps", task_id, len(plan))

            # --- Execution phase ---
            progress.set_status(TaskStatus.EXECUTING)
            result.started_at = datetime.now(timezone.utc)

            await self._ensure_session(profile=profile, headless=headless)
            self._otp = OTPHandler(self._session)

            await self.execute(result.steps, progress=progress)

            # --- Summary phase ---
            summary = await self._generate_summary(task_description, result.steps)
            progress.set_summary(summary)
            progress.mark_completed()

        except asyncio.TimeoutError:
            progress.mark_failed(f"Task timed out after {timeout_seconds}s")
        except Exception as exc:
            logger.exception("Task %s failed", task_id)
            progress.mark_failed(str(exc))
        finally:
            await self._cleanup_session()

        logger.info(
            "Task %s: finished — %s (%d/%d steps completed)",
            task_id,
            result.status.value,
            result.steps_completed,
            len(result.steps),
        )
        return result

    async def plan(
        self,
        task: str,
        extra_context: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Use the LLM to generate a step plan for the given task.

        Parameters
        ----------
        task : str
            Natural language task description.
        extra_context : str, optional
            Additional context to include in the planning prompt.

        Returns
        -------
        list[dict]
            Ordered list of step dictionaries with keys:
            ``action``, ``target``, ``value``, ``description``.
        """
        user_msg = task
        if extra_context:
            user_msg += f"\n\nAdditional context: {extra_context}"

        messages = [
            {"role": "system", "content": PLANNING_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ]

        raw = await self._llm_chat(messages, temperature=0.2)
        return self._parse_plan(raw)

    async def execute(
        self,
        steps: list[TaskStep],
        progress: Optional[TaskProgress] = None,
    ) -> list[dict[str, Any]]:
        """Execute a list of TaskSteps against the active browser session.

        Parameters
        ----------
        steps : list[TaskStep]
            Steps to execute in order.
        progress : TaskProgress, optional
            Progress tracker to update as steps complete.

        Returns
        -------
        list[dict]
            Per-step result dictionaries.
        """
        results: list[dict[str, Any]] = []

        for step in steps:
            if progress and progress.is_step_done(step.step_number):
                results.append({"step": step.step_number, "status": "already_done"})
                continue

            if progress:
                progress.start_step(step.step_number)

            logger.info(
                "Step %d: [%s] %s",
                step.step_number,
                step.action,
                step.description[:80],
            )

            try:
                output = await self._dispatch_action(step)
                step.status = StepStatus.COMPLETED
                step.result = str(output) if output else None

                if progress:
                    progress.complete_step(
                        step.step_number,
                        result_text=step.result,
                    )

                results.append(
                    {"step": step.step_number, "status": "completed", "output": output}
                )

            except Exception as exc:
                step.status = StepStatus.FAILED
                step.error = str(exc)
                logger.exception("Step %d failed", step.step_number)

                if progress:
                    progress.fail_step(step.step_number, str(exc))

                results.append(
                    {"step": step.step_number, "status": "failed", "error": str(exc)}
                )

                # Stop on critical failures
                if step.action in ("navigate",):
                    logger.error("Critical step failed — aborting remaining steps")
                    break

        return results

    # ------------------------------------------------------------------
    # Action dispatch
    # ------------------------------------------------------------------

    async def _dispatch_action(self, step: TaskStep) -> Any:
        """Route a single step to the appropriate browser action handler."""
        session = self._session
        if session is None:
            raise RuntimeError("No active browser session")

        action = step.action.lower()

        handlers = {
            "navigate": lambda: session.navigate(step.target or ""),
            "click": lambda: session.click(step.target or ""),
            "type": lambda: session.type_text(step.target or "", step.value or ""),
            "fill": lambda: session.fill(step.target or "", step.value or ""),
            "select": lambda: session.select_option(step.target or "", step.value or ""),
            "wait": lambda: session.wait_ms(int(step.value or "2000")),
            "wait_for_selector": lambda: session.wait_for_selector(step.target or ""),
            "screenshot": lambda: session.screenshot(),
            "extract_text": lambda: session.get_text(step.target or "body"),
            "scroll": lambda: session.scroll(step.value or "down"),
            "press_key": lambda: session.press_key(step.value or "Enter"),
            "hover": lambda: session.hover(step.target or ""),
            "upload_file": lambda: session.upload_file(step.target or "", step.value or ""),
            "evaluate": lambda: session.evaluate(step.value or ""),
            "otp_fill": lambda: self._otp.wait_and_fill() if self._otp else None,
            "assert_text": lambda: self._assert_text(step.target or "body", step.value or ""),
            "assert_visible": lambda: session.wait_for_selector(step.target or "", timeout=5000),
        }

        handler = handlers.get(action)
        if handler is None:
            raise ValueError(f"Unknown action: {action!r}")

        return await handler()

    async def _assert_text(self, selector: str, expected: str) -> bool:
        """Assert that the element contains the expected text."""
        actual = await self._session.get_text(selector)  # type: ignore[union-attr]
        if expected.lower() not in actual.lower():
            raise AssertionError(
                f"Expected text '{expected}' not found in '{actual[:200]}'"
            )
        return True

    # ------------------------------------------------------------------
    # LLM communication
    # ------------------------------------------------------------------

    async def _llm_chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> str:
        """Send a chat completion request to the OpenAI-compatible API."""
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=120.0)

        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        resp = await self._http.post(url, json=body, headers=headers)
        resp.raise_for_status()

        data = resp.json()
        return data["choices"][0]["message"]["content"]

    @staticmethod
    def _parse_plan(raw: str) -> list[dict[str, Any]]:
        """Parse the LLM response into a list of step dictionaries."""
        text = raw.strip()

        # Strip markdown code fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()

        try:
            plan = json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON array in the response
            start = text.find("[")
            end = text.rfind("]")
            if start != -1 and end != -1 and end > start:
                plan = json.loads(text[start : end + 1])
            else:
                raise ValueError(
                    f"LLM did not return a valid JSON plan. Response: {text[:500]}"
                )

        if not isinstance(plan, list):
            raise ValueError(f"Expected a JSON array, got {type(plan).__name__}")

        # Validate and normalize each step
        normalized: list[dict[str, Any]] = []
        for i, step in enumerate(plan):
            if not isinstance(step, dict):
                raise ValueError(f"Step {i} is not a dict: {step!r}")
            normalized.append(
                {
                    "action": step.get("action", "unknown"),
                    "target": step.get("target"),
                    "value": step.get("value"),
                    "description": step.get("description", f"Step {i}"),
                }
            )

        return normalized

    async def _generate_summary(
        self, task: str, steps: list[TaskStep]
    ) -> str:
        """Ask the LLM to summarize the task execution."""
        steps_data = [
            {
                "step": s.step_number,
                "action": s.action,
                "description": s.description,
                "status": s.status.value,
                "result": s.result,
                "error": s.error,
            }
            for s in steps
        ]

        prompt = SUMMARY_PROMPT.format(
            task=task, steps_json=json.dumps(steps_data, indent=2)
        )
        messages = [
            {"role": "system", "content": "You are a helpful assistant that summarizes browser automation results."},
            {"role": "user", "content": prompt},
        ]

        try:
            return await self._llm_chat(messages, temperature=0.3, max_tokens=500)
        except Exception:
            logger.warning("Failed to generate summary", exc_info=True)
            return f"Task completed {len([s for s in steps if s.status == StepStatus.COMPLETED])}/{len(steps)} steps."

    # ------------------------------------------------------------------
    # Browser session management
    # ------------------------------------------------------------------

    async def _ensure_session(
        self,
        profile: Optional[str] = None,
        headless: bool = True,
    ) -> None:
        """Start a browser session if one isn't already running."""
        if self._session is not None:
            return

        profile_path: Optional[str] = None
        if profile:
            if not self._profile_mgr.get_profile(profile):
                self._profile_mgr.create_profile(profile)
            if not self._profile_mgr.acquire(profile):
                raise RuntimeError(f"Profile '{profile}' is locked by another task")
            profile_path = str(self._profile_mgr._dir / profile)

        self._session = BrowserSession(
            profile_path=profile_path,
            headless=headless,
        )
        await self._session.start()

    async def _cleanup_session(self) -> None:
        """Stop the browser session and release resources."""
        if self._session:
            try:
                await self._session.stop()
            except Exception:
                logger.warning("Error stopping browser session", exc_info=True)
            self._session = None
        if self._http:
            await self._http.aclose()
            self._http = None

    # ------------------------------------------------------------------
    # Synchronous convenience wrapper
    # ------------------------------------------------------------------

    def run_sync(self, task_description: str, **kwargs: Any) -> TaskResult:
        """Synchronous wrapper around :meth:`run`.

        Creates a new event loop if necessary.  Useful for scripts and
        simple integrations that don't use ``async/await``.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # Already inside an async context — cannot use run_until_complete.
            # Fall back to a new thread with its own loop.
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, self.run(task_description, **kwargs))
                return future.result()
        else:
            return asyncio.run(self.run(task_description, **kwargs))
