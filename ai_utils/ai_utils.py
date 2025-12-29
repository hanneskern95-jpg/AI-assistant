from openai.types.responses.response import Response


def get_response_text(response: Response) -> str:
    """Extracts and returns the text content from an OpenAI response dictionary."""
    try:
        return response.output[1].content[0].text
    except (AttributeError, IndexError, TypeError):
        return ""