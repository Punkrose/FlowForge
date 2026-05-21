"""
FlowForge Engine - Core automation components.

This package contains the main automation logic:
- FlowForge: Main orchestrator that plans and executes tasks
- BrowserSession: Browser lifecycle management via CloakBrowser
- OTPHandler: One-time password detection and filling
- ProfileManager: Browser profile management with locking
- TaskProgress: Persistent task progress tracking
"""

from flowforge.engine.automator import FlowForge
from flowforge.engine.session import BrowserSession
from flowforge.engine.otp_handler import OTPHandler
from flowforge.engine.profile_manager import ProfileManager
from flowforge.engine.progress import TaskProgress

__all__ = [
    "FlowForge",
    "BrowserSession",
    "OTPHandler",
    "ProfileManager",
    "TaskProgress",
]
