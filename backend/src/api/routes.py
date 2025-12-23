"""API routes for the chat application.

All agent execution happens through Redis queue to the agent_service.
"""

import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from ..config import QUESTION_PROPOSALS, WELCOME_CONFIG, settings
from ..logging_config import get_logger
from ..utils import (
    create_error_event,
    enqueue_task,
    get_session_info,
    subscribe_task_events,
    validate_session_id,
)
from .dependencies import RedisDep, require_api_key
from .models import ChatRequest, HealthResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/ai/api", tags=["chat"])


@router.get("/welcome")
async def get_welcome_config() -> dict[str, Any]:
    """Get welcome screen configuration including title and suggestions.

    Returns:
        Dictionary with welcome config and question suggestions
    """
    return {
        "title": WELCOME_CONFIG["title"],
        "subtitle": WELCOME_CONFIG["subtitle"],
        "suggestions": QUESTION_PROPOSALS,
    }


@router.get("/suggestions")
async def get_suggestions(request: Request) -> list[str]:
    """Get question proposals for the welcome screen.

    Returns:
        List of suggested questions
    """
    return QUESTION_PROPOSALS


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request) -> dict[str, Any]:
    """Health check endpoint.

    Checks Redis and MCP server connectivity.

    Args:
        request: FastAPI request object

    Returns:
        Health status dictionary
    """
    # Check Redis connection
    redis_status = "skipped"
    if hasattr(request.app.state, "redis_client") and request.app.state.redis_client:
        try:
            await request.app.state.redis_client.client.ping()
            redis_status = "ok"
        except Exception as e:
            redis_status = f"error: {e}"

    # System is healthy if Redis (worker communication) is available
    overall = "healthy" if redis_status == "ok" else "degraded"

    return {
        "status": overall,
        "redis_status": redis_status,
    }


@router.post("/chat/stream", dependencies=[Depends(require_api_key)])
async def chat_stream(
    request: ChatRequest,
    http_request: Request,
    redis_client: RedisDep,
) -> EventSourceResponse:
    """Streaming chat endpoint using Redis queue for worker-based processing.

    Enqueues task to Redis and streams events from Pub/Sub.

    Args:
        request: Chat request with message and optional session_id
        http_request: HTTP request for disconnect detection
        redis_client: Redis client from dependency injection

    Returns:
        EventSourceResponse with SSE stream
    """
    # Validate and use provided session_id or generate new one
    validated_session_id = validate_session_id(request.session_id)
    session_id = validated_session_id or str(uuid4())

    logger.info(
        f"Stream request (session: {session_id[:8]}...): {request.message[:50]}..."
    )

    async def event_generator() -> AsyncGenerator[dict[str, str], Any]:
        """Generate SSE events from Redis Pub/Sub."""
        heartbeat_interval = 15
        last_beat = asyncio.get_event_loop().time()

        try:
            # Enqueue task to worker queue
            task_info = await enqueue_task(
                redis_client,
                message=request.message,
                session_id=session_id,
            )
            task_id = task_info["task_id"]

            # Initial session event
            event = {"type": "session", "session_id": session_id}
            yield {"event": "message", "data": json.dumps(event)}

            # Stream events from Redis Pub/Sub
            async for event in subscribe_task_events(redis_client, task_id):
                if await http_request.is_disconnected():
                    logger.info("Client disconnected from stream; stopping generator.")
                    break

                yield {"event": "message", "data": json.dumps(event)}

                # Send heartbeat periodically
                now = asyncio.get_event_loop().time()
                if now - last_beat >= heartbeat_interval:
                    last_beat = now
                    yield {"event": "heartbeat", "data": "keep-alive"}

                # Stop on terminal events
                if event.get("type") in ("complete", "error"):
                    break

        except Exception as e:
            logger.error(f"Error in stream: {e}", exc_info=True)
            error_event = create_error_event(str(e))
            yield {"event": "error", "data": json.dumps(error_event)}

    return EventSourceResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/session/{session_id}", dependencies=[Depends(require_api_key)])
async def get_session_details(session_id: str) -> dict[str, Any]:
    """Get session details including session data and metrics.

    Args:
        session_id: Session identifier (UUID format)

    Returns:
        Session information with metrics

    Raises:
        HTTPException: If session not found (404)
    """
    logger.info(f"Fetching session details: {session_id[:8]}...")

    session_info = get_session_info(settings.sessions_dir, session_id)

    if session_info is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    return session_info
