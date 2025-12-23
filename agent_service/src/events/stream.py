"""Stream event processing for agent responses."""

from typing import Any

from ..core import TOOL_MESSAGES
from ..utils import extract_final_response
from .workflow import process_assistant_message, process_user_message


def process_stream_event(
    event: dict[str, Any],
    pending_tools: dict[str, dict[str, Any]],
    workflow_steps: list[dict[str, Any]],
    step_counter: int,
) -> tuple[int, list[dict[str, Any]]]:
    """Process a single stream event and yield appropriate responses.

    Args:
        event: Stream event from agent
        pending_tools: Dictionary of pending tool executions
        workflow_steps: List of workflow steps
        step_counter: Current step counter

    Returns:
        Tuple of (updated_step_counter, list_of_events_to_yield)
    """
    events_to_yield: list[dict[str, Any]] = []

    # Stream text tokens
    if data := event.get("data"):
        events_to_yield.append({"type": "token", "content": data})

    # Handle current tool use (live streaming) - only track for pending
    if tool_use := event.get("current_tool_use"):
        tool_name = tool_use.get("name")
        tool_id = tool_use.get("toolUseId")

        if tool_id and tool_name:
            pending_tools[tool_id] = {
                "name": tool_name,
                "message": TOOL_MESSAGES.get(tool_name, f"⚙️ Running {tool_name}..."),
                "input": tool_use.get("input"),
            }

    # Process complete message events for workflow
    if msg := event.get("message"):
        if isinstance(msg, dict):
            role = msg.get("role")
            content_blocks = msg.get("content", [])

            if role == "assistant":
                step_counter = process_assistant_message(
                    content_blocks,
                    workflow_steps,
                    step_counter,
                    pending_tools,
                )

            elif role == "user":
                step_counter, tool_badges = process_user_message(
                    content_blocks,
                    pending_tools,
                    workflow_steps,
                    step_counter,
                )
                events_to_yield.extend(tool_badges)

    # Handle completion - batch workflow with complete event
    if result := event.get("result"):
        full_response = extract_final_response(result)

        complete_event: dict[str, Any] = {
            "type": "complete",
            "response": full_response,
        }

        if workflow_steps:
            complete_event["workflow"] = workflow_steps

        events_to_yield.append(complete_event)

    return step_counter, events_to_yield
