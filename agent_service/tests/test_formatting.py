"""Unit tests for formatting utilities."""

from src.utils.formatting import extract_final_response, format_error_message


class TestExtractFinalResponse:
    """Test extract_final_response function."""

    def test_extract_from_message_content(self) -> None:
        """Test extracting text from message content blocks."""

        class MockResult:
            message = {
                "content": [
                    {"text": "Hello "},
                    {"text": "World"},
                ]
            }

        result = extract_final_response(MockResult())
        assert result == "Hello World"

    def test_extract_empty_on_no_message(self) -> None:
        """Test empty string returned when no message."""

        class MockResult:
            pass

        result = extract_final_response(MockResult())
        assert result == ""

    def test_extract_empty_on_non_dict_message(self) -> None:
        """Test empty string when message is not dict."""

        class MockResult:
            message = "plain string"

        result = extract_final_response(MockResult())
        assert result == ""

    def test_extract_handles_missing_text(self) -> None:
        """Test handling of blocks without text."""

        class MockResult:
            message = {
                "content": [
                    {"other": "value"},
                    {"text": "Only this"},
                ]
            }

        result = extract_final_response(MockResult())
        assert result == "Only this"


class TestFormatErrorMessage:
    """Test format_error_message function."""

    def test_validation_exception(self) -> None:
        """Test formatting validation exception."""
        error = Exception("Some validationException error")
        result = format_error_message(error)
        # The function correctly detects validationException (case-insensitive)
        assert "Invalid request to AI model" in result

    def test_tool_call_parse_error(self) -> None:
        """Test formatting tool call parse error (exact match)."""
        error = Exception("error parsing tool call: failed")
        result = format_error_message(error)
        assert "formatting its response" in result

    def test_response_error(self) -> None:
        """Test formatting response error."""
        error = Exception("ResponseError: Connection failed")
        result = format_error_message(error)
        assert "communicating with the model" in result

    def test_generic_error_with_colon(self) -> None:
        """Test formatting generic error with colon."""
        error = Exception("ModuleError: Something specific happened")
        result = format_error_message(error)
        assert result == "An error occurred: ModuleError"

    def test_generic_error_without_colon(self) -> None:
        """Test formatting generic error without colon."""
        error = Exception("Simple error message")
        result = format_error_message(error)
        assert result == "An error occurred: Simple error message"
