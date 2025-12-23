"""Session management utilities."""

import json
from pathlib import Path
from typing import Any

from ..logging_config import get_logger

logger = get_logger(__name__)


def get_session_info(sessions_dir: str, session_id: str) -> dict[str, Any] | None:
    """Get session information including session data and all metrics.

    Args:
        sessions_dir: Directory containing session folders
        session_id: Session identifier

    Returns:
        Dictionary with session information and metrics, or None if not found
    """
    session_path = Path(sessions_dir) / f"session_{session_id}"
    if not session_path.exists():
        logger.debug(f"Session not found: {session_id}")
        return None

    info: dict[str, Any] = {"session_id": session_id}

    # Load session.json if it exists
    session_json = session_path / "session.json"
    if session_json.exists():
        try:
            with open(session_json) as f:
                session_data = json.load(f)
                info["session_data"] = session_data
                info["created_at"] = session_data.get("created_at")
                info["updated_at"] = session_data.get("updated_at")
        except Exception as e:
            logger.warning(f"Failed to load session.json for {session_id[:8]}: {e}")
            info["session_data"] = None

    # Load all metrics from the metrics directory
    metrics_dir = session_path / "metrics"
    if metrics_dir.exists() and metrics_dir.is_dir():
        metrics = []
        try:
            # Get all JSON files sorted by filename (timestamp)
            for metrics_file in sorted(metrics_dir.glob("*.json")):
                try:
                    with open(metrics_file) as f:
                        metrics.append(json.load(f))
                except Exception as e:
                    logger.warning(
                        f"Failed to load metric file {metrics_file.name}: {e}"
                    )

            if metrics:
                info["metrics"] = metrics
                info["metrics_count"] = len(metrics)

                # Aggregate accumulated usage and metrics across all entries
                total_usage: dict[str, float] = {}
                total_metrics: dict[str, float] = {}

                for metric in metrics:
                    # Sum accumulated_usage
                    if "accumulated_usage" in metric:
                        for key, value in metric["accumulated_usage"].items():
                            if isinstance(value, (int, float)):
                                total_usage[key] = (
                                    float(total_usage.get(key, 0)) + value
                                )

                    # Sum accumulated_metrics
                    if "accumulated_metrics" in metric:
                        for key, value in metric["accumulated_metrics"].items():
                            if isinstance(value, (int, float)):
                                total_metrics[key] = (
                                    float(total_metrics.get(key, 0)) + value
                                )

                if total_usage:
                    info["total_accumulated_usage"] = total_usage
                if total_metrics:
                    info["total_accumulated_metrics"] = total_metrics
        except Exception as e:
            logger.warning(f"Failed to load metrics for {session_id[:8]}: {e}")

    return info
