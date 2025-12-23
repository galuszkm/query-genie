"""Tests for agent manager cache eviction."""

import time
from collections.abc import Iterator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


class TestAgentCacheEviction:
    """Test agent cache TTL-based eviction."""

    @pytest.fixture
    def mock_settings(self, tmp_path: Any) -> Iterator[Any]:
        """Mock settings with short TTL for testing."""
        with patch("src.core.agent_manager.settings") as mock:
            mock.sessions_dir = str(tmp_path / "sessions")
            mock.session_ttl_hours = 1  # 1 hour TTL for tests
            mock.model_provider = "OLLAMA"
            mock.ollama_host = "http://localhost:11434"
            mock.ollama_model = "test-model"
            mock.mcp_server_url = "http://localhost:8000/mcp"
            yield mock

    @pytest.fixture
    def agent_manager(self, mock_settings: Any, tmp_path: Any) -> Iterator[Any]:
        """Create agent manager with mocked dependencies."""
        from src.core.agent_manager import AgentManager

        with (
            patch("src.core.agent_manager.OllamaModel"),
            patch("src.core.agent_manager.MCPClient"),
            patch("src.core.agent_manager.Path") as mock_path,
        ):
            mock_path.return_value.mkdir = MagicMock()
            manager = AgentManager()
            manager._model = MagicMock()
            manager._mcp_client = MagicMock()
            manager._mcp_client.__enter__ = MagicMock(return_value=manager._mcp_client)
            manager._mcp_client.list_tools_sync = MagicMock(return_value=[])
            manager._mcp_tools = []
            yield manager

    @pytest.fixture
    def agent_manager_with_real_paths(
        self, mock_settings: Any, tmp_path: Any
    ) -> Iterator[Any]:
        """Create agent manager with real filesystem for testing directory operations."""
        from src.core.agent_manager import AgentManager

        with (
            patch("src.core.agent_manager.OllamaModel"),
            patch("src.core.agent_manager.MCPClient"),
        ):
            manager = AgentManager()
            manager._model = MagicMock()
            manager._mcp_client = MagicMock()
            manager._mcp_client.__enter__ = MagicMock(return_value=manager._mcp_client)
            manager._mcp_client.list_tools_sync = MagicMock(return_value=[])
            manager._mcp_tools = []
            yield manager

    def test_agent_last_access_tracked_on_creation(self, agent_manager: Any) -> None:
        """Test that last access time is set when agent is created."""
        session_id = "test-session-1"

        with patch("src.core.agent_manager.Agent"):
            agent_manager.get_or_create_agent(session_id)

        assert session_id in agent_manager._agent_last_access
        assert isinstance(agent_manager._agent_last_access[session_id], float)

    def test_agent_last_access_updated_on_reuse(self, agent_manager: Any) -> None:
        """Test that last access time is updated when agent is reused."""
        session_id = "test-session-2"

        with patch("src.core.agent_manager.Agent"):
            # Create agent
            agent_manager.get_or_create_agent(session_id)
            first_access = agent_manager._agent_last_access[session_id]

            # Simulate time passing
            time.sleep(0.1)

            # Access agent again
            agent_manager.get_or_create_agent(session_id)
            second_access = agent_manager._agent_last_access[session_id]

        assert second_access > first_access

    def test_cleanup_removes_stale_agents(
        self, agent_manager: Any, mock_settings: Any
    ) -> None:
        """Test that stale agents are removed during cleanup."""
        with patch("src.core.agent_manager.Agent"):
            # Create two agents
            agent_manager.get_or_create_agent("fresh-session")
            agent_manager.get_or_create_agent("stale-session")

            # Manually set one agent as stale (older than TTL)
            ttl_seconds = mock_settings.session_ttl_hours * 3600
            agent_manager._agent_last_access["stale-session"] = (
                time.time() - ttl_seconds - 100
            )

            # Run cleanup
            agent_manager.cleanup_stale_agents()

        # Stale agent should be removed
        assert "stale-session" not in agent_manager._agents
        assert "stale-session" not in agent_manager._agent_last_access

        # Fresh agent should remain
        assert "fresh-session" in agent_manager._agents
        assert "fresh-session" in agent_manager._agent_last_access

    def test_cleanup_removes_multiple_stale_agents(
        self, agent_manager: Any, mock_settings: Any
    ) -> None:
        """Test that multiple stale agents are removed in one cleanup."""
        with patch("src.core.agent_manager.Agent"):
            # Create fresh and stale agents
            agent_manager.get_or_create_agent("fresh-1")
            agent_manager.get_or_create_agent("fresh-2")
            agent_manager.get_or_create_agent("stale-1")
            agent_manager.get_or_create_agent("stale-2")
            agent_manager.get_or_create_agent("stale-3")

            # Mark three agents as stale
            ttl_seconds = mock_settings.session_ttl_hours * 3600
            old_time = time.time() - ttl_seconds - 100
            agent_manager._agent_last_access["stale-1"] = old_time
            agent_manager._agent_last_access["stale-2"] = old_time
            agent_manager._agent_last_access["stale-3"] = old_time

            # Run cleanup
            agent_manager.cleanup_stale_agents()

        # All stale agents removed
        assert "stale-1" not in agent_manager._agents
        assert "stale-2" not in agent_manager._agents
        assert "stale-3" not in agent_manager._agents

        # Fresh agents remain
        assert "fresh-1" in agent_manager._agents
        assert "fresh-2" in agent_manager._agents
        assert len(agent_manager._agents) == 2

    def test_remove_agent_clears_last_access(self, agent_manager: Any) -> None:
        """Test that removing an agent also clears its last access time."""
        session_id = "test-session-3"

        with patch("src.core.agent_manager.Agent"):
            agent_manager.get_or_create_agent(session_id)
            assert session_id in agent_manager._agent_last_access

            agent_manager.remove_agent(session_id)
            assert session_id not in agent_manager._agent_last_access

    def test_shutdown_clears_last_access_dict(self, agent_manager: Any) -> None:
        """Test that shutdown clears the last access tracking dictionary."""
        with patch("src.core.agent_manager.Agent"):
            agent_manager.get_or_create_agent("session-1")
            agent_manager.get_or_create_agent("session-2")

            assert len(agent_manager._agent_last_access) == 2

            agent_manager.shutdown()

            assert len(agent_manager._agent_last_access) == 0
            assert len(agent_manager._agents) == 0

    def test_remove_agent_deletes_session_directory(
        self, agent_manager_with_real_paths: Any, tmp_path: Any
    ) -> None:
        """Test that removing an agent also deletes the session directory."""
        session_id = "test-session-dir-1"

        with patch("src.core.agent_manager.Agent"):
            # Create agent (which will create session directory)
            agent_manager_with_real_paths.get_or_create_agent(session_id)

            # Manually create the session directory since Agent is mocked
            session_dir = tmp_path / "sessions" / f"session_{session_id}"
            session_dir.mkdir(parents=True, exist_ok=True)

            # Verify session directory exists
            assert session_dir.exists()

            # Remove agent
            agent_manager_with_real_paths.remove_agent(session_id)

            # Verify session directory is deleted
            assert not session_dir.exists()

    def test_cleanup_stale_agents_removes_session_directories(
        self, agent_manager_with_real_paths: Any, mock_settings: Any, tmp_path: Any
    ) -> None:
        """Test that cleanup removes session directories for stale agents."""
        with patch("src.core.agent_manager.Agent"):
            # Create agents (which will create session directories)
            agent_manager_with_real_paths.get_or_create_agent("fresh-session")
            agent_manager_with_real_paths.get_or_create_agent("stale-session")

            # Manually create session directories since Agent is mocked
            fresh_dir = tmp_path / "sessions" / "session_fresh-session"
            stale_dir = tmp_path / "sessions" / "session_stale-session"
            fresh_dir.mkdir(parents=True, exist_ok=True)
            stale_dir.mkdir(parents=True, exist_ok=True)

            # Verify both directories exist
            assert fresh_dir.exists()
            assert stale_dir.exists()

            # Mark one agent as stale
            ttl_seconds = mock_settings.session_ttl_hours * 3600
            agent_manager_with_real_paths._agent_last_access["stale-session"] = (
                time.time() - ttl_seconds - 100
            )

            # Run cleanup
            agent_manager_with_real_paths.cleanup_stale_agents()

        # Stale session directory should be removed
        assert not stale_dir.exists()

        # Fresh session directory should remain
        assert fresh_dir.exists()
