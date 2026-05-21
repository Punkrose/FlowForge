"""
BrowserSession - Browser lifecycle management via CloakBrowser.

Wraps CloakBrowser's persistent context to provide a clean interface for
page navigation, element interaction, screenshots, and waiting strategies.
"""

from __future__ import annotations

import asyncio
import base64
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

SCREENSHOT_DIR = Path.home() / ".flowforge" / "screenshots"


class BrowserSession:
    """Manage a stealth browser session using CloakBrowser.

    This class owns the browser lifecycle: launching, creating pages,
    taking screenshots, and cleaning up resources.

    Parameters
    ----------
    profile_path : str, optional
        Filesystem path for persistent browser profile data.
    headless : bool
        Run the browser without a visible window (default ``True``).
    """

    def __init__(
        self,
        profile_path: Optional[str] = None,
        headless: bool = True,
    ) -> None:
        self._profile_path = profile_path
        self._headless = headless
        self._context: Any = None
        self._page: Any = None
        self._browser: Any = None
        self._screenshot_dir = SCREENSHOT_DIR
        self._screenshot_dir.mkdir(parents=True, exist_ok=True)
        self._step_counter: int = 0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Launch the browser and open a new page.

        Uses ``cloakbrowser`` for stealth browsing. If the package is not
        installed, falls back to standard Playwright Chromium.
        """
        try:
            from cloakbrowser import CloakBrowser  # type: ignore[import-untyped]

            self._browser = CloakBrowser()
            self._context = await self._browser.start(
                headless=self._headless,
                user_data_dir=self._profile_path,
            )
            logger.info("Started CloakBrowser (headless=%s)", self._headless)
        except ImportError:
            logger.warning(
                "cloakbrowser not installed — falling back to Playwright Chromium"
            )
            from playwright.async_api import async_playwright

            pw = await async_playwright().start()
            launch_args = [
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
            ]
            self._browser = await pw.chromium.launch(
                headless=self._headless,
                args=launch_args,
            )
            context_opts: dict[str, Any] = {
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            }
            if self._profile_path:
                context_opts["user_data_dir"] = self._profile_path
                context_opts["storage_state"] = None
            self._context = await self._browser.new_context(**context_opts)
            logger.info("Started Playwright Chromium (headless=%s)", self._headless)

        self._page = await self._context.new_page()
        logger.info("Browser session ready")

    async def stop(self) -> None:
        """Close the browser and release all resources."""
        try:
            if self._context:
                await self._context.close()
            if self._browser and hasattr(self._browser, "close"):
                await self._browser.close()
            logger.info("Browser session stopped")
        except Exception:
            logger.exception("Error while stopping browser session")
        finally:
            self._page = None
            self._context = None
            self._browser = None

    # ------------------------------------------------------------------
    # Page access
    # ------------------------------------------------------------------

    @property
    def page(self) -> Any:
        """Return the active Playwright Page object."""
        if self._page is None:
            raise RuntimeError("Browser session is not started. Call start() first.")
        return self._page

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    async def navigate(self, url: str, wait_until: str = "domcontentloaded") -> None:
        """Navigate to *url* and wait for the given load state."""
        logger.info("Navigating to %s", url)
        await self.page.goto(url, wait_until=wait_until, timeout=60_000)

    # ------------------------------------------------------------------
    # Interaction helpers
    # ------------------------------------------------------------------

    async def click(self, selector: str, timeout: float = 10_000) -> None:
        """Click the element matching *selector*."""
        await self.page.click(selector, timeout=timeout)

    async def type_text(self, selector: str, text: str, delay: float = 50) -> None:
        """Type *text* into the element matching *selector*, keystroke by keystroke."""
        await self.page.click(selector, timeout=10_000)
        await self.page.type(selector, text, delay=delay)

    async def fill(self, selector: str, value: str) -> None:
        """Fill *value* into the input matching *selector* (fast, no keystroke simulation)."""
        await self.page.fill(selector, value)

    async def select_option(self, selector: str, value: str) -> None:
        """Choose *value* from a <select> element."""
        await self.page.select_option(selector, value)

    async def press_key(self, key: str) -> None:
        """Press a keyboard key (e.g. ``Enter``, ``Tab``)."""
        await self.page.keyboard.press(key)

    async def hover(self, selector: str) -> None:
        """Hover over the element matching *selector*."""
        await self.page.hover(selector)

    async def scroll(self, direction: str = "down", amount: int = 500) -> None:
        """Scroll the page in the given direction."""
        delta = amount if direction == "down" else -amount
        await self.page.mouse.wheel(0, delta)

    async def evaluate(self, expression: str) -> Any:
        """Evaluate a JavaScript expression in the page context."""
        return await self.page.evaluate(expression)

    async def upload_file(self, selector: str, file_path: str) -> None:
        """Upload a file to a file input element."""
        await self.page.set_input_files(selector, file_path)

    # ------------------------------------------------------------------
    # Waiting
    # ------------------------------------------------------------------

    async def wait_for_selector(
        self, selector: str, timeout: float = 30_000, state: str = "visible"
    ) -> None:
        """Wait until the element matching *selector* is in the given *state*."""
        await self.page.wait_for_selector(selector, timeout=timeout, state=state)

    async def wait_for_load(self, state: str = "networkidle", timeout: float = 30_000) -> None:
        """Wait until the page reaches the given load *state*."""
        await self.page.wait_for_load_state(state, timeout=timeout)

    async def wait_ms(self, milliseconds: int) -> None:
        """Sleep for the given number of milliseconds."""
        await asyncio.sleep(milliseconds / 1000)

    # ------------------------------------------------------------------
    # Screenshots & content extraction
    # ------------------------------------------------------------------

    async def screenshot(
        self,
        name: Optional[str] = None,
        full_page: bool = True,
    ) -> str:
        """Capture a screenshot and return the file path.

        Parameters
        ----------
        name : str, optional
            Custom filename (without extension). Auto-generated if omitted.
        full_page : bool
            Capture the full scrollable page.
        """
        self._step_counter += 1
        filename = name or f"step_{self._step_counter}_{datetime.now(timezone.utc).strftime('%H%M%S')}"
        path = self._screenshot_dir / f"{filename}.png"
        await self.page.screenshot(path=str(path), full_page=full_page)
        logger.info("Screenshot saved: %s", path)
        return str(path)

    async def screenshot_base64(self, full_page: bool = True) -> str:
        """Capture a screenshot and return it as a base64-encoded string."""
        raw = await self.page.screenshot(full_page=full_page, type="png")
        return base64.b64encode(raw).decode("ascii")

    async def get_text(self, selector: str) -> str:
        """Extract text content from the element matching *selector*."""
        return await self.page.inner_text(selector)

    async def get_page_text(self) -> str:
        """Extract visible text from the entire page body."""
        return await self.page.inner_text("body")

    async def get_url(self) -> str:
        """Return the current page URL."""
        return self.page.url

    async def get_title(self) -> str:
        """Return the current page title."""
        return await self.page.title()

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "BrowserSession":
        await self.start()
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.stop()
