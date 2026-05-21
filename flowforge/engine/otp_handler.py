"""
OTPHandler - One-time password detection, fetching, and filling.

Supports:
- Detecting OTP input widgets on web pages.
- Filling OTP codes manually or from email.
- Fetching OTP codes from Gmail using the Gmail API.
"""

from __future__ import annotations

import asyncio
import base64
import email
import logging
import re
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Common CSS selectors for OTP input fields
OTP_SELECTORS = [
    'input[autocomplete="one-time-code"]',
    'input[name*="otp"]',
    'input[name*="code"]',
    'input[name*="token"]',
    'input[name*="verification"]',
    'input[placeholder*="code"]',
    'input[placeholder*="OTP"]',
    'input[placeholder*="verification"]',
    'input[type="tel"][maxlength="6"]',
    'input[type="number"][maxlength="6"]',
    'input[pattern="[0-9]*"][maxlength="6"]',
]

# Common OTP-related keywords for heuristic detection
OTP_KEYWORDS = [
    "verification code",
    "one-time code",
    "one time code",
    "otp",
    "security code",
    "confirm code",
    "enter code",
    "verification number",
    "auth code",
]


class OTPHandler:
    """Detect and fill one-time password fields on web pages.

    Parameters
    ----------
    session : BrowserSession
        The active browser session to operate on.
    gmail_service : object, optional
        An authenticated Gmail API service object for fetching OTP emails.
    """

    def __init__(
        self,
        session: Any,
        gmail_service: Optional[Any] = None,
    ) -> None:
        self._session = session
        self._gmail = gmail_service

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------

    async def detect_otp_widget(self) -> Optional[str]:
        """Attempt to find an OTP input field on the current page.

        Returns the CSS selector of the first matching input, or ``None``
        if no OTP widget is detected.
        """
        page = self._session.page

        # Strategy 1: Try well-known OTP selectors
        for selector in OTP_SELECTORS:
            try:
                el = await page.query_selector(selector)
                if el and await el.is_visible():
                    logger.info("Detected OTP widget via selector: %s", selector)
                    return selector
            except Exception:
                continue

        # Strategy 2: Look for visible input near OTP-related text
        try:
            body_text = (await self._session.get_page_text()).lower()
            has_otp_context = any(kw in body_text for kw in OTP_KEYWORDS)
            if has_otp_context:
                # Find the first visible text/number input
                inputs = await page.query_selector_all(
                    'input[type="text"], input[type="number"], input[type="tel"], input:not([type])'
                )
                for inp in inputs:
                    if await inp.is_visible():
                        max_len = await inp.get_attribute("maxlength")
                        if max_len and int(max_len) <= 8:
                            # Derive a unique selector
                            name = await inp.get_attribute("name")
                            if name:
                                sel = f'input[name="{name}"]'
                            else:
                                sel = "input:focus"  # will need prior click
                            logger.info("Detected OTP widget via heuristic: %s", sel)
                            return sel
        except Exception:
            logger.debug("Heuristic OTP detection failed", exc_info=True)

        logger.warning("No OTP widget detected on the page")
        return None

    # ------------------------------------------------------------------
    # Filling
    # ------------------------------------------------------------------

    async def fill_otp(self, code: str, selector: Optional[str] = None) -> bool:
        """Fill an OTP code into the detected or specified input.

        Parameters
        ----------
        code : str
            The OTP code to enter.
        selector : str, optional
            CSS selector for the OTP input. Auto-detected if omitted.

        Returns
        -------
        bool
            True if the code was filled successfully.
        """
        if selector is None:
            selector = await self.detect_otp_widget()
        if selector is None:
            logger.error("Cannot fill OTP: no widget detected")
            return False

        try:
            # Clear any existing value and type the code
            await self._session.fill(selector, code)
            logger.info("Filled OTP code '%s' into %s", code, selector)

            # Many OTP forms auto-submit; otherwise press Enter
            await asyncio.sleep(0.5)
            await self._session.press_key("Enter")
            return True
        except Exception:
            logger.exception("Failed to fill OTP code")
            return False

    # ------------------------------------------------------------------
    # Gmail OTP fetching
    # ------------------------------------------------------------------

    async def fetch_email_otp(
        self,
        gmail_query: str = "is:unread subject:code",
        max_wait_seconds: int = 120,
        poll_interval: int = 5,
    ) -> Optional[str]:
        """Poll Gmail for an OTP code matching *gmail_query*.

        Parameters
        ----------
        gmail_query : str
            Gmail search query to find the OTP email.
        max_wait_seconds : int
            How long to wait for the email to arrive.
        poll_interval : int
            Seconds between polling attempts.

        Returns
        -------
        str or None
            The extracted OTP code, or None if not found within the timeout.
        """
        if self._gmail is None:
            logger.error("Gmail service not configured. Set gmail_service on init.")
            return None

        elapsed = 0
        while elapsed < max_wait_seconds:
            code = await self._search_gmail_for_otp(gmail_query)
            if code:
                return code
            logger.debug(
                "OTP email not found yet, retrying in %ds (%d/%ds)",
                poll_interval, elapsed, max_wait_seconds,
            )
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        logger.warning("OTP email not found within %ds", max_wait_seconds)
        return None

    async def _search_gmail_for_otp(self, query: str) -> Optional[str]:
        """Search Gmail and extract an OTP code from the latest matching email."""
        try:
            results = self._gmail.users().messages().list(
                userId="me", q=query, maxResults=1
            ).execute()

            messages = results.get("messages", [])
            if not messages:
                return None

            msg_id = messages[0]["id"]
            msg = (
                self._gmail.users()
                .messages()
                .get(userId="me", id=msg_id, format="full")
                .execute()
            )
            return self._extract_otp_from_message(msg)
        except Exception:
            logger.exception("Gmail API error while searching for OTP")
            return None

    @staticmethod
    def _extract_otp_from_message(msg: dict[str, Any]) -> Optional[str]:
        """Extract a numeric OTP code from a Gmail message payload."""
        payload = msg.get("payload", {})
        body_data = ""

        # Try direct body
        if "body" in payload and payload["body"].get("data"):
            body_data = base64.urlsafe_b64decode(payload["body"]["data"]).decode(
                "utf-8", errors="replace"
            )

        # Try parts (multipart email)
        if not body_data:
            for part in payload.get("parts", []):
                if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                    body_data = base64.urlsafe_b64decode(part["body"]["data"]).decode(
                        "utf-8", errors="replace"
                    )
                    break
                elif part.get("mimeType") == "text/html" and part.get("body", {}).get("data"):
                    body_data = base64.urlsafe_b64decode(part["body"]["data"]).decode(
                        "utf-8", errors="replace"
                    )

        if not body_data:
            return None

        # Look for 4-8 digit codes
        patterns = [
            r"verification code[:\s]*(\d{4,8})",
            r"code[:\s]*(\d{4,8})",
            r"OTP[:\s]*(\d{4,8})",
            r"(\d{6})",  # Most common OTP length
            r"(\d{4,8})",
        ]
        for pattern in patterns:
            match = re.search(pattern, body_data, re.IGNORECASE)
            if match:
                code = match.group(1)
                logger.info("Extracted OTP code from email: %s", code)
                return code

        return None

    # ------------------------------------------------------------------
    # Convenience: wait and fill
    # ------------------------------------------------------------------

    async def wait_and_fill(
        self,
        gmail_query: str = "is:unread subject:code",
        otp_selector: Optional[str] = None,
        max_wait_seconds: int = 120,
    ) -> bool:
        """Wait for an OTP email to arrive, then fill it into the page.

        This is the high-level convenience method that combines
        :meth:`fetch_email_otp` and :meth:`fill_otp`.

        Parameters
        ----------
        gmail_query : str
            Gmail search query for the OTP email.
        otp_selector : str, optional
            CSS selector for the OTP input. Auto-detected if omitted.
        max_wait_seconds : int
            Maximum time to wait for the email.

        Returns
        -------
        bool
            True if the OTP was successfully fetched and filled.
        """
        code = await self.fetch_email_otp(
            gmail_query=gmail_query,
            max_wait_seconds=max_wait_seconds,
        )
        if code is None:
            return False
        return await self.fill_otp(code, selector=otp_selector)
