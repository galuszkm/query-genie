"""Unit tests for stream processing utilities."""

from typing import Any

from src.events.stream import process_stream_event


class TestProcessStreamEvent:
    """Test process_stream_event function."""

    def test_process_token_event(self) -> None:
        """Test processing a token streaming event."""
        event = {"data": "Hello"}
        pending_tools: dict[str, dict[str, Any]] = {}
        workflow_steps: list[dict[str, Any]] = []
        step_counter = 0

        new_counter, events = process_stream_event(
            event, pending_tools, workflow_steps, step_counter
        )

        assert new_counter == 0
        assert len(events) == 1
        assert events[0]["type"] == "token"
        assert events[0]["content"] == "Hello"

    def test_process_tool_use_event(self) -> None:
        """Test processing a tool use event."""
        event = {
            "current_tool_use": {
                "name": "query",
                "toolUseId": "tool-123",
                "input": {"query": "SELECT 1"},
            }
        }
        pending_tools: dict[str, dict[str, Any]] = {}
        workflow_steps: list[dict[str, Any]] = []
        step_counter = 0

        new_counter, events = process_stream_event(
            event, pending_tools, workflow_steps, step_counter
        )

        assert new_counter == 0
        assert len(events) == 0  # Tool use doesn't yield events directly
        assert "tool-123" in pending_tools
        assert pending_tools["tool-123"]["name"] == "query"

    def test_process_complete_event(self) -> None:
        """Test processing a completion event."""

        # Create a mock result object that extract_final_response can read
        class MockResult:
            message = {"content": [{"text": "Done!"}]}

        event = {"result": MockResult()}
        pending_tools: dict[str, dict[str, Any]] = {}
        workflow_steps: list[dict[str, Any]] = []
        step_counter = 0

        new_counter, events = process_stream_event(
            event, pending_tools, workflow_steps, step_counter
        )

        assert len(events) == 1
        assert events[0]["type"] == "complete"
        assert events[0]["response"] == "Done!"

    def test_process_multiple_tokens(self) -> None:
        """Test that multiple tokens maintain state correctly."""
        pending_tools: dict[str, dict[str, Any]] = {}
        workflow_steps: list[dict[str, Any]] = []
        step_counter = 0

        # Process multiple token events
        tokens = ["Hello", " ", "World"]
        all_events = []
        for token in tokens:
            event = {"data": token}
            step_counter, events = process_stream_event(
                event, pending_tools, workflow_steps, step_counter
            )
            all_events.extend(events)

        assert len(all_events) == 3
        assert all(e["type"] == "token" for e in all_events)
        assert [e["content"] for e in all_events] == tokens

    def test_empty_event(self) -> None:
        """Test processing an empty event."""
        event: dict[str, Any] = {}
        pending_tools: dict[str, dict[str, Any]] = {}
        workflow_steps: list[dict[str, Any]] = []
        step_counter = 0

        new_counter, events = process_stream_event(
            event, pending_tools, workflow_steps, step_counter
        )

        assert new_counter == 0
        assert len(events) == 0
