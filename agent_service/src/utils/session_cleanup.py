"""Session cleanup utilities for managing session directory growth.

Automatically removes expired sessions based on TTL and enforces max session limits.
"""

import shutil
import time
from pathlib import Path

from .logging_config import get_logger

logger = get_logger(__name__)


def remove_session_directory(sessions_dir: str, session_id: str) -> None:
    """Remove a single session directory from disk.

    Args:
        sessions_dir: Base directory containing session folders
        session_id: Session identifier (without 'session_' prefix)
    """
    session_path = Path(sessions_dir) / f"session_{session_id}"
    if session_path.exists():
        try:
            shutil.rmtree(session_path, ignore_errors=True)
            logger.debug(f"Removed session directory: {session_path.name}")
        except Exception as e:
            logger.error(f"Failed to remove session directory {session_path.name}: {e}")


def cleanup_sessions(sessions_dir: str, ttl_hours: int, max_sessions: int) -> None:
    """Remove expired sessions and enforce max session count.

    Removes sessions in two passes:
    1. Delete sessions older than TTL (based on directory modification time)
    2. If still over max_sessions, delete oldest sessions to stay within limit

    Args:
        sessions_dir: Directory containing session folders (session_*)
        ttl_hours: Time-to-live in hours for sessions
        max_sessions: Maximum number of sessions to keep
    """
    session_root = Path(sessions_dir)
    if not session_root.exists():
        logger.debug(f"Sessions directory does not exist: {sessions_dir}")
        return

    # Find all session directories
    sessions: list[tuple[float, Path]] = []
    for path in session_root.glob("session_*"):
        if path.is_dir():
            mtime = path.stat().st_mtime
            sessions.append((mtime, path))

    if not sessions:
        logger.debug("No sessions found to cleanup")
        return

    logger.info(f"Starting session cleanup: {len(sessions)} sessions found")

    now = time.time()
    ttl_seconds = ttl_hours * 3600

    # Pass 1: Remove expired sessions
    filtered_sessions: list[tuple[float, Path]] = []
    removed_count = 0
    for mtime, path in sessions:
        age_hours = (now - mtime) / 3600
        if now - mtime > ttl_seconds:
            try:
                shutil.rmtree(path, ignore_errors=True)
                removed_count += 1
                logger.info(
                    f"Removed expired session: {path.name} (age: {age_hours:.1f}h)"
                )
            except Exception as e:
                logger.error(f"Failed to remove session {path.name}: {e}")
        elif path.exists():
            filtered_sessions.append((mtime, path))

    if removed_count > 0:
        logger.info(f"Cleanup: Removed {removed_count} expired sessions")

    # Pass 2: Enforce max count
    if len(filtered_sessions) > max_sessions:
        # Sort by modification time (oldest first)
        filtered_sessions.sort(key=lambda t: t[0])
        overflow = len(filtered_sessions) - max_sessions

        for _, path in filtered_sessions[:overflow]:
            try:
                shutil.rmtree(path, ignore_errors=True)
                logger.info(f"Removed old session (max limit): {path.name}")
            except Exception as e:
                logger.error(f"Failed to remove session {path.name}: {e}")

        logger.info(
            f"Cleanup: Removed {overflow} sessions to enforce max limit "
            f"({max_sessions} sessions)"
        )

    remaining = len(filtered_sessions) - (
        overflow if len(filtered_sessions) > max_sessions else 0
    )
    logger.info(f"Session cleanup complete: {remaining} sessions remaining")
