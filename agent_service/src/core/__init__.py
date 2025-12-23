"""Core agent service functionality.

Contains:
- Agent manager for lifecycle and caching
- Configuration settings
- System prompts
"""

from .agent_manager import AgentManager
from .config import TOOL_MESSAGES, settings
from .prompts import SYSTEM_PROMPT

__all__ = [
    "AgentManager",
    "settings",
    "TOOL_MESSAGES",
    "SYSTEM_PROMPT",
]
