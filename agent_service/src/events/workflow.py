"""Workflow processing utilities for handling agent reasoning and tool execution."""

from typing import Any

from ..core import TOOL_MESSAGES

# Maximum output length for workflow steps (to prevent large SSE payloads)
MAX_OUTPUT_LENGTH = 5000


def extract_reasoning_content(block: dict[str, Any]) -> str:
    """Extract reasoning text from a reasoning content block.

    Args:
        block: Content block containing reasoning data

    Returns:
        Extracted reasoning text
    """
    reasoning = block.get("reasoningContent", {})
    if not isinstance(reasoning, dict):
        return ""

    if "reasoningText" in reasoning:
        rt = reasoning["reasoningText"]
        return rt.get("text", "") if isinstance(rt, dict) else str(rt)
    if "text" in reasoning:
        return str(reasoning["text"])

    return ""


def extract_tool_output(tool_content: Any) -> str:
    """Extract output text from tool result content.

    Args:
        tool_content: Tool result content (list or string)

    Returns:
        Extracted output text
    """
    output_text = ""
    if isinstance(tool_content, list):
        for item in tool_content:
            if isinstance(item, dict) and "text" in item:
                output_text += item["text"]
    elif isinstance(tool_content, str):
        output_text = tool_content
    return output_text


def truncate_output(output: str, max_length: int = MAX_OUTPUT_LENGTH) -> str:
    """Truncate output to prevent large SSE payloads.

    Args:
        output: Output text to truncate
        max_length: Maximum length before truncation

    Returns:
        Truncated output with ellipsis if needed
    """
    if len(output) <= max_length:
        return output

    # Find a good break point (newline near the limit)
    truncate_at = max_length
    last_newline = output.rfind("\n", max_length - 500, max_length)
    if last_newline > 0:
        truncate_at = last_newline

    truncated = output[:truncate_at].rstrip()
    line_count = output.count("\n") + 1
    truncated_lines = truncated.count("\n") + 1
    remaining = line_count - truncated_lines

    return f"{truncated}\n\n... (truncated {remaining} more lines, {len(output) - truncate_at} more characters)"


def handle_reasoning_block(
    block: dict[str, Any], workflow_steps: list[dict[str, Any]], step_counter: int
) -> int:
    """Process reasoning content block and add to workflow steps.

    Args:
        block: Reasoning content block
        workflow_steps: List to append workflow steps
        step_counter: Current step counter

    Returns:
        Updated step counter
    """
    reasoning_text = extract_reasoning_content(block)
    if reasoning_text.strip():
        step_counter += 1
        workflow_steps.append(
            {
                "step": step_counter,
                "type": "reasoning",
                "content": reasoning_text,
            }
        )
    return step_counter


def handle_tool_use_block(
    block: dict[str, Any],
    pending_tools: dict[str, dict[str, Any]],
) -> None:
    """Process tool use block and track pending tools.

    Args:
        block: Tool use content block
        pending_tools: Dictionary to track pending tool executions
    """
    tool_use_block = block.get("toolUse", {})
    tool_id = tool_use_block.get("toolUseId")
    tool_name = tool_use_block.get("name")

    if not (tool_id and tool_name):
        return

    tool_info = {
        "name": tool_name,
        "message": TOOL_MESSAGES.get(tool_name, f"⚙️ Running {tool_name} ..."),
        "input": tool_use_block.get("input"),
    }
    pending_tools[tool_id] = tool_info


def handle_tool_result_block(
    block: dict[str, Any],
    pending_tools: dict[str, dict[str, Any]],
    workflow_steps: list[dict[str, Any]],
    step_counter: int,
) -> tuple[int, dict[str, Any] | None]:
    """Process tool result block, add to workflow steps, and return tool badge.

    Args:
        block: Tool result content block
        pending_tools: Dictionary of pending tool executions
        workflow_steps: List to append workflow steps
        step_counter: Current step counter

    Returns:
        Tuple of (updated_step_counter, tool_badge_or_none)
    """
    tool_result = block.get("toolResult", {})
    tool_id = tool_result.get("toolUseId")
    tool_content = tool_result.get("content", [])
    output_text = extract_tool_output(tool_content)

    # Match with pending tool
    tool_info = None
    if tool_id and tool_id in pending_tools:
        tool_info = pending_tools.pop(tool_id)
    elif pending_tools:
        # Fallback to oldest pending tool
        fallback_id = next(iter(pending_tools))
        tool_info = pending_tools.pop(fallback_id)

    tool_badge = None
    if tool_info:
        step_counter += 1

        # Truncate output to prevent large SSE payloads
        if output_text:
            truncated_output = truncate_output(output_text)
        elif tool_content:
            content_str = (
                str(tool_content) if not isinstance(tool_content, str) else tool_content
            )
            truncated_output = truncate_output(content_str)
        else:
            truncated_output = ""

        workflow_steps.append(
            {
                "step": step_counter,
                "type": "tool",
                "name": tool_info["name"],
                "message": tool_info["message"],
                "input": tool_info["input"],
                "output": truncated_output,
                "status": tool_result.get("status", "success"),
                "tool_use_id": tool_id,
            }
        )
        tool_badge = {
            "type": "tool",
            "name": tool_info["name"],
            "message": tool_info["message"],
            "input": tool_info.get("input"),
            "tool_use_id": tool_id,
        }

    return step_counter, tool_badge


def process_assistant_message(
    content_blocks: list[Any],
    workflow_steps: list[dict[str, Any]],
    step_counter: int,
    pending_tools: dict[str, dict[str, Any]],
) -> int:
    """Process assistant message content blocks (tracks pending tools).

    Args:
        content_blocks: List of content blocks from assistant message
        workflow_steps: List to append workflow steps
        step_counter: Current step counter
        pending_tools: Dictionary to track pending tool executions

    Returns:
        Updated step counter
    """
    for block in content_blocks:
        if not isinstance(block, dict):
            continue

        if "reasoningContent" in block:
            step_counter = handle_reasoning_block(block, workflow_steps, step_counter)

        if "toolUse" in block:
            handle_tool_use_block(block, pending_tools)

    return step_counter


def process_user_message(
    content_blocks: list[Any],
    pending_tools: dict[str, dict[str, Any]],
    workflow_steps: list[dict[str, Any]],
    step_counter: int,
) -> tuple[int, list[dict[str, Any]]]:
    """Process user message content blocks (tool results).

    Args:
        content_blocks: List of content blocks from user message
        pending_tools: Dictionary of pending tool executions
        workflow_steps: List to append workflow steps
        step_counter: Current step counter

    Returns:
        Tuple of (updated_step_counter, list_of_tool_badges)
    """
    tool_badges = []

    for block in content_blocks:
        if not isinstance(block, dict):
            continue

        if "toolResult" in block:
            step_counter, badge = handle_tool_result_block(
                block, pending_tools, workflow_steps, step_counter
            )
            if badge:
                tool_badges.append(badge)

    return step_counter, tool_badges
