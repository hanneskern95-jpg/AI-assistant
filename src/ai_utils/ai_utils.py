"""Utilities for working with OpenAI response objects.

This module contains small helpers to safely extract text content from
response objects returned by the OpenAI client. The helpers are
defensive: they handle missing or unexpected fields and return an
empty string when text cannot be extracted.
"""

from openai.types.responses.response import Response


def get_response_text(response: Response) -> str:
    """Extract the primary text content from an OpenAI ``Response``.

    The function attempts to read the most common location for model
    output text on the provided ``response`` object.

    Args:
        response (Response): An OpenAI SDK response object.

    Returns:
        str: The extracted text if available, otherwise an empty
        string.
    """
    try:
        return response.output[1].content[0].text
    except (AttributeError, IndexError, TypeError):
        return ""