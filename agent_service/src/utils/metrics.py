"""Metrics handling for agent service."""

import json
import time
from pathlib import Path
from typing import Any

from strands import Agent

from .logging_config import get_logger

logger = get_logger(__name__)


def save_metrics(sessions_dir: str, session_id: str, agent: Agent) -> None:
    """Save agent metrics to a timestamped JSON file.

    Args:
        sessions_dir: Base directory for session storage
        session_id: Session identifier
        agent: Agent with event_loop_metrics
    """
    try:
        metrics_summary = agent.event_loop_metrics.get_summary()

        # Remove traces to reduce file size
        metrics_summary.pop("traces", None)

        # Create metrics directory
        session_path = Path(sessions_dir) / f"session_{session_id}"
        metrics_dir = session_path / "metrics"
        metrics_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename with timestamp
        timestamp = int(time.time() * 1000)
        metrics_file = metrics_dir / f"{timestamp}.json"

        # Save metrics
        with open(metrics_file, "w") as f:
            json.dump(metrics_summary, f, indent=2)

        logger.debug(f"Saved metrics to {metrics_file}")
    except Exception as e:
        logger.warning(f"Failed to save metrics for {session_id[:8]}: {e}")


def get_metrics(sessions_dir: str, session_id: str) -> list[dict[str, Any]]:
    """Load all metrics for a session.

    Args:
        sessions_dir: Base directory for session storage
        session_id: Session identifier

    Returns:
        List of metrics dictionaries
    """
    session_path = Path(sessions_dir) / f"session_{session_id}"
    metrics_dir = session_path / "metrics"

    if not metrics_dir.exists():
        return []

    metrics = []
    for metrics_file in sorted(metrics_dir.glob("*.json")):
        try:
            with open(metrics_file) as f:
                metrics.append(json.load(f))
        except Exception as e:
            logger.warning(f"Failed to load metric file {metrics_file.name}: {e}")

    return metrics
