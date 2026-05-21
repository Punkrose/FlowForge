"""
FlowForge - AI-Powered Browser Automation Framework

FlowForge uses large language models to plan and execute browser automation
tasks from natural language descriptions. Built on top of CloakBrowser for
stealth browser automation with persistent profiles.
"""

__version__ = "0.1.0"
__author__ = "FlowForge Contributors"
__license__ = "MIT"

from flowforge.engine.automator import FlowForge
from flowforge.models.task import TaskCreate, TaskResult, TaskStep, ProfileInfo

__all__ = [
    "FlowForge",
    "TaskCreate",
    "TaskResult",
    "TaskStep",
    "ProfileInfo",
    "__version__",
]
