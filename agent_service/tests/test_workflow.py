"""Unit tests for workflow processing utilities."""

from typing import Any

from src.events.workflow import (
    extract_reasoning_content,
    extract_tool_output,
    handle_reasoning_block,
    handle_tool_result_block,
    handle_tool_use_block,
    process_assistant_message,
    process_user_message,
    truncate_output,
)


class TestExtractReasoningContent:
    """Test extract_reasoning_content function."""

    def test_extract_with_reasoning_text(self) -> None:
        """Test extraction from reasoningText structure."""
        block = {
            "reasoningContent": {
                "reasoningText": {"text": "I need to check the database"}
            }
        }
        result = extract_reasoning_content(block)
        assert result == "I need to check the database"

    def test_extract_with_direct_text(self) -> None:
        """Test extraction from direct text structure."""
        block = {"reasoningContent": {"text": "Direct reasoning text"}}
        result = extract_reasoning_content(block)
        assert result == "Direct reasoning text"

    def test_empty_block(self) -> None:
        """Test with empty or missing content."""
        assert extract_reasoning_content({}) == ""
        assert extract_reasoning_content({"reasoningContent": {}}) == ""

    def test_non_dict_reasoning(self) -> None:
        """Test with non-dict reasoning content."""
        block = {"reasoningContent": "not a dict"}
        assert extract_reasoning_content(block) == ""


class TestExtractToolOutput:
    """Test extract_tool_output function."""

    def test_extract_from_list(self) -> None:
        """Test extraction from list of text items."""
        content = [
            {"text": "First part"},
            {"text": " Second part"},
        ]
        result = extract_tool_output(content)
        assert result == "First part Second part"

    def test_extract_from_string(self) -> None:
        """Test extraction from direct string."""
        content = "Direct string output"
        result = extract_tool_output(content)
        assert result == "Direct string output"

    def test_empty_list(self) -> None:
        """Test with empty list."""
        assert extract_tool_output([]) == ""

    def test_list_without_text(self) -> None:
        """Test with list items missing text."""
        content = [{"other": "value"}]
        result = extract_tool_output(content)
        assert result == ""


class TestTruncateOutput:
    """Test truncate_output function."""

    def test_short_output_unchanged(self) -> None:
        """Test that short output is not truncated."""
        short_text = "Short text"
        result = truncate_output(short_text, max_length=100)
        assert result == short_text

    def test_long_output_truncated(self) -> None:
        """Test that long output is truncated."""
        long_text = "A" * 6000
        result = truncate_output(long_text, max_length=5000)
        assert len(result) < 6000
        assert "truncated" in result

    def test_truncation_at_exact_length_unchanged(self) -> None:
        """Test output at exact max length is not truncated."""
        text = "A" * 5000
        result = truncate_output(text, max_length=5000)
        # At exactly max_length, no truncation
        assert result == text


class TestHandleReasoningBlock:
    """Test handle_reasoning_block function."""

    def test_adds_reasoning_step(self) -> None:
        """Test that reasoning is added to workflow steps."""
        block = {
            "reasoningContent": {"reasoningText": {"text": "Thinking about the query"}}
        }
        workflow_steps: list[dict[str, Any]] = []
        step_counter = 0

        new_counter = handle_reasoning_block(block, workflow_steps, step_counter)

        assert new_counter == 1
        assert len(workflow_steps) == 1
        assert workflow_steps[0]["type"] == "reasoning"
        assert workflow_steps[0]["content"] == "Thinking about the query"
        assert workflow_steps[0]["step"] == 1

    def test_empty_reasoning_not_added(self) -> None:
        """Test that empty reasoning is not added."""
        block = {"reasoningContent": {"reasoningText": {"text": "   "}}}
        workflow_steps: list[dict[str, Any]] = []
        step_counter = 0

        new_counter = handle_reasoning_block(block, workflow_steps, step_counter)

        assert new_counter == 0
        assert len(workflow_steps) == 0


class TestHandleToolUseBlock:
    """Test handle_tool_use_block function."""

    def test_tracks_pending_tool(self) -> None:
        """Test that tool use is tracked in pending tools."""
        block = {
            "toolUse": {
                "toolUseId": "tool-123",
                "name": "query",
                "input": {"query": "SELECT 1"},
            }
        }
        pending_tools: dict[str, dict[str, Any]] = {}

        handle_tool_use_block(block, pending_tools)

        assert "tool-123" in pending_tools
        assert pending_tools["tool-123"]["name"] == "query"
        # Tool message comes from config TOOL_MESSAGES
        assert "message" in pending_tools["tool-123"]

    def test_missing_tool_id(self) -> None:
        """Test that missing tool ID is handled."""
        block = {"toolUse": {"name": "query"}}
        pending_tools: dict[str, dict[str, Any]] = {}

        handle_tool_use_block(block, pending_tools)

        assert len(pending_tools) == 0


class TestHandleToolResultBlock:
    """Test handle_tool_result_block function."""

    def test_matches_pending_tool(self) -> None:
        """Test that result matches pending tool and creates badge."""
        pending_tools: dict[str, dict[str, Any]] = {
            "tool-123": {
                "name": "query",
                "message": "🔎 Querying",
                "input": {"query": "SELECT 1"},
            }
        }
        block = {
            "toolResult": {
                "toolUseId": "tool-123",
                "content": [{"text": "Result: 1 row"}],
                "status": "success",
            }
        }
        workflow_steps: list[dict[str, Any]] = []

        new_counter, badge = handle_tool_result_block(
            block, pending_tools, workflow_steps, 0
        )

        assert new_counter == 1
        assert badge is not None
        assert badge["type"] == "tool"
        assert badge["name"] == "query"
        assert len(workflow_steps) == 1
        assert workflow_steps[0]["status"] == "success"

    def test_no_pending_tool(self) -> None:
        """Test with no matching pending tool."""
        block = {
            "toolResult": {
                "toolUseId": "unknown",
                "content": [],
            }
        }
        pending_tools: dict[str, dict[str, Any]] = {}
        workflow_steps: list[dict[str, Any]] = []

        new_counter, badge = handle_tool_result_block(
            block, pending_tools, workflow_steps, 0
        )

        assert badge is None
        assert len(workflow_steps) == 0


class TestProcessAssistantMessage:
    """Test process_assistant_message function."""

    def test_processes_reasoning_and_tool(self) -> None:
        """Test processing message with reasoning and tool use."""
        content_blocks = [
            {"reasoningContent": {"reasoningText": {"text": "Need to query database"}}},
            {
                "toolUse": {
                    "toolUseId": "t1",
                    "name": "query",
                    "input": {},
                }
            },
        ]
        workflow_steps: list[dict[str, Any]] = []
        pending_tools: dict[str, dict[str, Any]] = {}

        counter = process_assistant_message(
            content_blocks, workflow_steps, 0, pending_tools
        )

        assert counter == 1  # One reasoning step
        assert "t1" in pending_tools


class TestProcessUserMessage:
    """Test process_user_message function."""

    def test_processes_tool_results(self) -> None:
        """Test processing user message with tool results."""
        pending_tools: dict[str, dict[str, Any]] = {
            "t1": {"name": "query", "message": "🔎 Querying", "input": {}}
        }
        content_blocks = [
            {
                "toolResult": {
                    "toolUseId": "t1",
                    "content": [{"text": "Done"}],
                    "status": "success",
                }
            }
        ]
        workflow_steps: list[dict[str, Any]] = []

        counter, badges = process_user_message(
            content_blocks, pending_tools, workflow_steps, 0
        )

        assert counter == 1
        assert len(badges) == 1
        assert badges[0]["type"] == "tool"
