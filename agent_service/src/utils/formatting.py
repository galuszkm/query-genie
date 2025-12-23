"""Response formatting utilities for agent service."""

from typing import Any


def extract_final_response(result: Any) -> str:
    """Extract full text response from result object.

    Args:
        result: Agent result object with message content

    Returns:
        Extracted text response
    """
    full_response = ""
    if result_msg := getattr(result, "message", None):
        if isinstance(result_msg, dict):
            for block in result_msg.get("content", []):
                if isinstance(block, dict) and "text" in block:
                    full_response += block["text"]
    return full_response


def format_error_message(error: Exception) -> str:
    """Format error message for user display.

    Args:
        error: Exception to format

    Returns:
        User-friendly error message
    """
    error_msg = str(error)

    if "validationexception" in error_msg.lower():
        return "Invalid request to AI model. Please check model configuration or try a different request."
    if "error parsing tool call" in error_msg.lower():
        return "The model had trouble formatting its response. Please try rephrasing your question."
    if "responseerror" in error_msg.lower():
        return "There was an error communicating with the model. Please try again."

    # Generic error: show first part before colon
    if ":" in error_msg:
        return f"An error occurred: {error_msg.split(':')[0]}"
    return f"An error occurred: {error_msg}"
