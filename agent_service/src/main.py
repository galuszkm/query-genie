"""Agent service entry point.

Main module that:
- Listens for tasks from Redis queue (BRPOP)
- Processes agent requests with streaming events
- Publishes SSE events to Redis Pub/Sub for frontend delivery
- Handles task cancellation when users disconnect
"""

import asyncio
import json
from typing import Any

import redis.asyncio as redis

from .core import AgentManager, settings
from .events import (
    create_redis_client,
    is_task_cancelled,
    pop_task,
    process_stream_event,
)
from .utils import (
    cleanup_sessions,
    configure_logging,
    format_error_message,
    get_logger,
    save_metrics,
)

logger = get_logger(__name__)


class TaskProcessor:
    """Processes agent tasks from Redis queue.

    Consumes tasks, executes AI agent operations, and publishes
    streaming events to Redis Pub/Sub for frontend delivery.
    """

    def __init__(self) -> None:
        """Initialize the task processor."""
        self._redis: redis.Redis | None = None
        self._agent_manager = AgentManager()
        self._cleanup_task: asyncio.Task[None] | None = None

    async def initialize(self) -> None:
        """Initialize connections to Redis and agent manager.

        Must be called before processing tasks.
        """
        logger.info("Initializing task processor...")

        # Initialize Redis connection
        self._redis = await create_redis_client()

        # Initialize agent manager (model, MCP)
        self._agent_manager.initialize()

        # Run initial cleanup (sessions and agents)
        cleanup_sessions(
            settings.sessions_dir,
            settings.session_ttl_hours,
            settings.session_max_sessions,
        )
        self._agent_manager.cleanup_stale_agents()

        # Start background cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        logger.info("Task processor initialized successfully")

    async def _cleanup_loop(self) -> None:
        """Background task that periodically cleans up expired sessions and stale agents."""
        interval_seconds = settings.session_cleanup_interval_minutes * 60
        logger.info(
            f"Cleanup task started "
            f"(interval: {settings.session_cleanup_interval_minutes}min, "
            f"TTL: {settings.session_ttl_hours}h, "
            f"max sessions: {settings.session_max_sessions})"
        )

        while True:
            try:
                await asyncio.sleep(interval_seconds)
                logger.debug("Running periodic cleanup...")

                # Clean up session files from disk
                cleanup_sessions(
                    settings.sessions_dir,
                    settings.session_ttl_hours,
                    settings.session_max_sessions,
                )

                # Clean up stale agents from memory cache
                self._agent_manager.cleanup_stale_agents()

            except asyncio.CancelledError:
                logger.info("Cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}", exc_info=True)

    async def process_task(self, task: dict[str, Any]) -> None:
        """Process a single agent task.

        Streams events to Redis Pub/Sub using the same format as current SSE.
        Checks for cancellation periodically during streaming.

        Args:
            task: Task dictionary with task_id, session_id, message
        """
        task_id = task["task_id"]
        session_id = task["session_id"]
        message = task["message"]

        logger.info(f"Processing task {task_id[:8]} for session {session_id[:8]}")

        # Publish session acknowledgment
        await self._publish(task_id, {"type": "session", "session_id": session_id})

        agent = self._agent_manager.get_or_create_agent(session_id)

        pending_tools: dict[str, dict[str, Any]] = {}
        workflow_steps: list[dict[str, Any]] = []
        step_counter = 0

        try:
            # Stream agent response
            async for event in agent.stream_async(message):
                # Check for cancellation
                if self._redis and await is_task_cancelled(self._redis, task_id):
                    logger.info(f"Task {task_id[:8]} cancelled by user")
                    await self._publish(
                        task_id,
                        {
                            "type": "error",
                            "message": "Request cancelled by user",
                            "session_id": session_id,
                        },
                    )
                    return

                step_counter, events = process_stream_event(
                    event,
                    pending_tools,
                    workflow_steps,
                    step_counter,
                )

                for event_data in events:
                    if event_data.get("type") == "complete":
                        event_data["session_id"] = session_id
                    await self._publish(task_id, event_data)

            # Save metrics after completion
            save_metrics(
                self._agent_manager.sessions_dir,
                session_id,
                agent,
            )
            logger.info(f"Task {task_id[:8]} completed successfully")

        except Exception as e:
            logger.error(f"Task {task_id[:8]} failed: {e}", exc_info=True)
            await self._publish(
                task_id,
                {
                    "type": "error",
                    "message": format_error_message(e),
                    "session_id": session_id,
                },
            )

    async def _publish(self, task_id: str, event: dict[str, Any]) -> None:
        """Publish event to Redis Pub/Sub channel.

        Args:
            task_id: Task identifier
            event: Event data to publish
        """
        if not self._redis:
            return

        channel = f"task:{task_id}"
        event_json = json.dumps(event)
        await self._redis.publish(channel, event_json)
        logger.debug(f"Published event to {channel}: {event.get('type')}")

    async def run(self) -> None:
        """Main worker loop - listen for tasks and process them.

        Uses BRPOP for blocking wait on task queue.
        BRPOP blocks until an item is available, preventing CPU waste.
        """
        if not self._redis:
            raise RuntimeError("Worker not initialized. Call initialize() first.")

        queue = settings.redis_task_queue
        logger.info(f"Worker listening on queue: {queue}")

        while True:
            try:
                # BRPOP blocks until task available (timeout=0 means forever)
                task = await pop_task(self._redis, queue, timeout=0)

                if task:
                    await self.process_task(task)

            except asyncio.CancelledError:
                logger.info("Worker received shutdown signal")
                break
            except Exception as e:
                logger.error(f"Error processing task: {e}", exc_info=True)
                # Continue processing other tasks
                await asyncio.sleep(1)

    async def shutdown(self) -> None:
        """Cleanup resources on shutdown."""
        logger.info("Shutting down task processor...")

        # Cancel cleanup task
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Shutdown agent manager
        self._agent_manager.shutdown()

        # Close Redis connection
        if self._redis:
            await self._redis.close()
            logger.info("Redis connection closed")

        logger.info("Task processor shut down")


async def run_worker() -> None:
    """Entry point for running the agent service."""
    configure_logging(level="INFO")
    logger.info("Starting agent service...")

    processor = TaskProcessor()
    await processor.initialize()

    try:
        await processor.run()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        await processor.shutdown()


if __name__ == "__main__":
    asyncio.run(run_worker())
