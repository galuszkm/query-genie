"""Agent manager for creating and caching agents per session.

Handles:
- Model initialization (Bedrock, Ollama, or OpenAI)
- MCP client setup
- Agent creation with session persistence
- Agent cache eviction based on TTL
"""

import time
from pathlib import Path
from typing import Any

from mcp.client.streamable_http import streamable_http_client
from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.models.bedrock import BedrockModel
from strands.models.ollama import OllamaModel
from strands.models.openai import OpenAIModel
from strands.session.file_session_manager import FileSessionManager
from strands.tools.mcp import MCPClient
from strands_tools import calculator

from ..utils import get_logger
from ..utils.session_cleanup import remove_session_directory
from .config import settings
from .prompts import SYSTEM_PROMPT

logger = get_logger(__name__)


class AgentManager:
    """Manages agent lifecycle and caching per session.

    Agents are cached by session_id to maintain conversation context.
    Uses shared model and MCP tools across all agents.

    Cache eviction:
    - Agents are removed after SESSION_TTL_HOURS of inactivity
    - Last access time tracked on each get_or_create_agent call
    - Cleanup runs periodically via cleanup_stale_agents()
    """

    def __init__(self) -> None:
        """Initialize agent manager."""
        self._model: OllamaModel | BedrockModel | OpenAIModel | None = None
        self._mcp_client: MCPClient | None = None
        self._mcp_tools: list[Any] = []
        self._agents: dict[str, Agent] = {}
        self._agent_last_access: dict[str, float] = {}  # session_id -> timestamp
        self._sessions_dir = settings.sessions_dir
        Path(self._sessions_dir).mkdir(parents=True, exist_ok=True)

    def initialize(self) -> None:
        """Initialize model and MCP client.

        Must be called before getting agents.
        """
        self._init_model()
        self._init_mcp_client()
        logger.info("Agent manager initialized")

    def _init_model(self) -> None:
        """Initialize the LLM model (Bedrock, Ollama, or OpenAI)."""
        if settings.model_provider == "BEDROCK":
            self._model = BedrockModel(
                boto_session=settings.get_bedrock_boto_session(),
                model_id=settings.bedrock_model,
            )
            logger.info(f"Initialized Bedrock model: {settings.bedrock_model}")
        elif settings.model_provider == "OLLAMA":
            self._model = OllamaModel(
                host=settings.ollama_host,
                model_id=settings.ollama_model,
                options={
                    "num_ctx": 16384,
                    "num_gpu": -1,
                    "num_batch": 512,
                    "temperature": 0.4,
                    "top_p": 0.9,
                    "repeat_penalty": 1.05,
                },
            )
            logger.info(f"Initialized Ollama model: {settings.ollama_model}")
        elif settings.model_provider == "OPENAI":
            self._model = OpenAIModel(
                client_args={"api_key": settings.openai_api_key.get_secret_value()},
                model_id=settings.openai_model,
            )
            logger.info(f"Initialized OpenAI model: {settings.openai_model}")
        else:
            raise ValueError(f"Unsupported MODEL_PROVIDER: {settings.model_provider}")

    def _init_mcp_client(self) -> None:
        """Initialize MCP client and cache tools."""
        try:
            self._mcp_client = MCPClient(
                lambda: streamable_http_client(url=settings.mcp_server_url)
            )
            self._mcp_client.__enter__()
            self._mcp_tools = self._mcp_client.list_tools_sync()
            logger.info(f"MCP client initialized with {len(self._mcp_tools)} tools")
        except Exception as e:
            logger.error(f"Failed to initialize MCP client: {e}", exc_info=True)
            raise RuntimeError(f"MCP client initialization failed: {e}") from e

    def get_or_create_agent(self, session_id: str) -> Agent:
        """Get existing agent for session or create a new one.

        Updates last access time for cache eviction policy.

        Args:
            session_id: Unique session identifier

        Returns:
            Agent instance with session context
        """
        if session_id in self._agents:
            logger.debug(f"Reusing cached agent for session {session_id[:8]}")
            # Update last access time
            self._agent_last_access[session_id] = time.time()
            return self._agents[session_id]

        logger.info(f"Creating new agent for session {session_id[:8]}")

        # Combine MCP tools with local tools
        tools = self._mcp_tools + [calculator]

        # Use FileSessionManager for conversation persistence
        session_manager = FileSessionManager(
            session_id=session_id,
            storage_dir=self._sessions_dir,
        )

        # Sliding window to manage long conversations
        conversation_manager = SlidingWindowConversationManager(
            window_size=40,
            should_truncate_results=False,
        )

        agent = Agent(
            model=self._model,
            tools=tools,
            system_prompt=SYSTEM_PROMPT,
            session_manager=session_manager,
            conversation_manager=conversation_manager,
        )

        self._agents[session_id] = agent
        self._agent_last_access[session_id] = time.time()
        return agent

    def remove_agent(self, session_id: str) -> None:
        """Remove agent from cache and clean up session directory.

        Args:
            session_id: Session identifier
        """
        if session_id in self._agents:
            del self._agents[session_id]
            self._agent_last_access.pop(session_id, None)
            remove_session_directory(self._sessions_dir, session_id)
            logger.debug(f"Removed agent and session for {session_id[:8]}")

    def cleanup_stale_agents(self) -> None:
        """Remove agents that have been inactive for longer than SESSION_TTL_HOURS.

        This method should be called periodically (e.g., in background task)
        to prevent unbounded memory growth from cached agents.
        """
        now = time.time()
        ttl_seconds = settings.session_ttl_hours * 3600
        stale_sessions = []

        for session_id, last_access in self._agent_last_access.items():
            age_seconds = now - last_access
            if age_seconds > ttl_seconds:
                stale_sessions.append(session_id)

        for session_id in stale_sessions:
            age_hours = (now - self._agent_last_access[session_id]) / 3600
            logger.info(
                f"Removing stale agent for session {session_id[:8]} "
                f"(inactive for {age_hours:.1f}h)"
            )
            self.remove_agent(session_id)

        if stale_sessions:
            logger.info(
                f"Agent cache cleanup: removed {len(stale_sessions)} stale agents, "
                f"{len(self._agents)} agents remaining"
            )

    @property
    def sessions_dir(self) -> str:
        """Get sessions directory path."""
        return self._sessions_dir

    def shutdown(self) -> None:
        """Cleanup resources."""
        if self._mcp_client:
            try:
                self._mcp_client.__exit__(None, None, None)
                logger.info("MCP client closed")
            except Exception as e:
                logger.error(f"Error closing MCP client: {e}")

        self._agents.clear()
        self._agent_last_access.clear()
        logger.info("Agent manager shut down")
