"""Tests for session utilities."""

import json
from typing import Any


class TestGetSessionInfo:
    """Tests for get_session_info utility."""

    def test_returns_combined_session_data(self, tmp_path: Any) -> None:
        """Test successful session data retrieval with metrics."""
        from src.utils.session import get_session_info

        # Create test session directory structure
        sessions_dir = tmp_path / "strands_sessions"
        session_dir = sessions_dir / "session_test-123"
        session_dir.mkdir(parents=True)
        metrics_dir = session_dir / "metrics"
        metrics_dir.mkdir()

        # Create session.json
        session_data = {"session_id": "test-123", "created_at": "2024-01-01T00:00:00Z"}
        (session_dir / "session.json").write_text(json.dumps(session_data))

        # Create metric files
        metric1 = {
            "accumulated_usage": {"total_tokens": 50},
            "accumulated_metrics": {"duration_ms": 500},
        }
        (metrics_dir / "metric_1.json").write_text(json.dumps(metric1))

        metric2 = {
            "accumulated_usage": {"total_tokens": 30},
            "accumulated_metrics": {"duration_ms": 300},
        }
        (metrics_dir / "metric_2.json").write_text(json.dumps(metric2))

        result = get_session_info(str(sessions_dir), "test-123")

        assert result is not None
        assert result["session_id"] == "test-123"
        assert result["total_accumulated_usage"]["total_tokens"] == 80
        assert result["total_accumulated_metrics"]["duration_ms"] == 800

    def test_returns_none_for_missing_session(self, tmp_path: Any) -> None:
        """Test returns None when session doesn't exist."""
        from src.utils.session import get_session_info

        sessions_dir = tmp_path / "strands_sessions"
        sessions_dir.mkdir()

        result = get_session_info(str(sessions_dir), "nonexistent-session")
        assert result is None

    def test_handles_session_without_metrics(self, tmp_path: Any) -> None:
        """Test session data without metrics directory."""
        from src.utils.session import get_session_info

        # Create test session without metrics
        sessions_dir = tmp_path / "strands_sessions"
        session_dir = sessions_dir / "session_test-456"
        session_dir.mkdir(parents=True)

        session_data = {"session_id": "test-456"}
        (session_dir / "session.json").write_text(json.dumps(session_data))

        result = get_session_info(str(sessions_dir), "test-456")

        assert result is not None
        assert result["session_id"] == "test-456"
        # When there are no metrics, the aggregate keys won't be present
        assert "metrics" not in result or result.get("metrics", []) == []

    def test_handles_invalid_metric_files(self, tmp_path: Any) -> None:
        """Test gracefully handles corrupted metric files."""
        from src.utils.session import get_session_info

        sessions_dir = tmp_path / "strands_sessions"
        session_dir = sessions_dir / "session_test-789"
        session_dir.mkdir(parents=True)
        metrics_dir = session_dir / "metrics"
        metrics_dir.mkdir()

        session_data = {"session_id": "test-789"}
        (session_dir / "session.json").write_text(json.dumps(session_data))

        # Create invalid metric file
        (metrics_dir / "bad_metric.json").write_text("invalid json{")

        result = get_session_info(str(sessions_dir), "test-789")

        # Should still return session data even with bad metric file
        assert result is not None
        assert result["session_id"] == "test-789"
