"""Unit tests for agent service metrics handling."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from src.utils.metrics import get_metrics, save_metrics


class TestSaveMetrics:
    """Test save_metrics function."""

    def test_saves_metrics_to_json_file(self) -> None:
        """Test that metrics are saved to a timestamped JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_agent = MagicMock()
            mock_agent.event_loop_metrics.get_summary.return_value = {
                "total_tokens": 100,
                "latency_ms": 500,
                "traces": ["trace1", "trace2"],  # Should be removed
            }

            save_metrics(tmpdir, "session-123", mock_agent)

            # Check metrics directory was created
            session_path = Path(tmpdir) / "session_session-123"
            metrics_dir = session_path / "metrics"
            assert metrics_dir.exists()

            # Check metrics file was created
            metric_files = list(metrics_dir.glob("*.json"))
            assert len(metric_files) == 1

            # Check traces were removed
            with open(metric_files[0]) as f:
                saved_metrics = json.load(f)
            assert "traces" not in saved_metrics
            assert saved_metrics["total_tokens"] == 100

    def test_handles_save_error_gracefully(self) -> None:
        """Test that save errors are handled without raising."""
        mock_agent = MagicMock()
        mock_agent.event_loop_metrics.get_summary.side_effect = Exception("Mock error")

        # Should not raise
        save_metrics("/invalid/path", "session-123", mock_agent)


class TestGetMetrics:
    """Test get_metrics function."""

    def test_returns_empty_list_when_no_metrics(self) -> None:
        """Test that empty list is returned when no metrics exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = get_metrics(tmpdir, "nonexistent-session")
            assert result == []

    def test_loads_all_metrics_files(self) -> None:
        """Test that all metrics files are loaded and sorted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "session_session-123"
            metrics_dir = session_path / "metrics"
            metrics_dir.mkdir(parents=True)

            # Create two metric files with different timestamps
            metric1 = {"tokens": 50}
            metric2 = {"tokens": 100}

            with open(metrics_dir / "1000.json", "w") as f:
                json.dump(metric1, f)
            with open(metrics_dir / "2000.json", "w") as f:
                json.dump(metric2, f)

            result = get_metrics(tmpdir, "session-123")

            assert len(result) == 2
            # Should be sorted by filename (timestamp)
            assert result[0]["tokens"] == 50
            assert result[1]["tokens"] == 100

    def test_handles_corrupt_json_gracefully(self) -> None:
        """Test that corrupt JSON files don't crash loading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "session_session-123"
            metrics_dir = session_path / "metrics"
            metrics_dir.mkdir(parents=True)

            # Create one valid and one invalid file
            with open(metrics_dir / "1000.json", "w") as f:
                json.dump({"tokens": 50}, f)
            with open(metrics_dir / "2000.json", "w") as f:
                f.write("not valid json{{{")

            result = get_metrics(tmpdir, "session-123")

            # Should load the valid file
            assert len(result) == 1
            assert result[0]["tokens"] == 50
