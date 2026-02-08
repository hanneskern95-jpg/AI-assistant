"""Wikipedia fact-checking tool.

This module implements a tool that queries the web (Wikipedia) to
verify a user's factual claim or to provide a citation from Wikipedia.
The tool is intended to be invoked only when the user explicitly
requests verification or a Wikipedia citation; it returns a small
JSON-shaped result describing whether a relevant article was found
and whether that article answers the user's question.
"""

import json
import re

from openai import OpenAI

from ai_utils import get_response_text
from tool_base import AnswerDict, Tool


class WikipediaFactCheckerTool(Tool):
    """Tool that searches Wikipedia and produces a structured result.

    The tool uses the OpenAI responses API with a web search tool to
    locate and read a relevant Wikipedia article. It returns a small
    JSON structure indicating the extracted answer (or null), a link
    to the article (or null), and an enum-like ``article_answers_question``
    which is one of ``'Yes'``, ``'Inconclusive'``, or
    ``'NoArticleFound'``.

    Attributes:
        _system_prompt (str): System prompt describing the tool's role.
        _model (str): Model name to use for the responses API.
        _openai (OpenAI): OpenAI client instance used to call the API.
        _result (dict | None): Last parsed JSON result from the model.
    """

    def __init__(self, model: str, openai: OpenAI) -> None:
        """Create a new WikipediaFactCheckerTool.

        Args:
            model (str): The model identifier passed to the responses API.
            openai (OpenAI): An initialized OpenAI client instance.

        Returns:
            None
        """
        self.tool_dict = {
            "type": "function",
            "name": "check_fact_wikipedia",
            "description": (
                "Only call this function when the user explicitly requests verification or a citation from Wikipedia, "
                "or asks what Wikipedia says about a claim or topic. Do NOT call this function for ordinary factual "
                "questions the assistant can answer directly (e.g., simple math, definitions, translations, or general "
                "explanations). Triggers: user asks 'What does Wikipedia say about...', 'fact-check', 'verify with Wikipedia', "
                "'is it true that...', or explicitly requests a Wikipedia source. Non-triggers: routine knowledge queries, "
                "conversational replies, or operational instructions. When called, return ONLY the JSON described in the schema below. "
                "JSON format expected: {\n  'answer': string|null,\n  'wikipedia_link': string|null,\n  'article_answers_question': 'Yes'|'Inconclusive'|'NoArticleFound'\n}\n\n"
                "Definitions:"
                "'Yes' — the located Wikipedia article directly and conclusively answers the user's question (the article contains a clear statement or verifiable data that addresses the claim). "
                "'Inconclusive' — a relevant Wikipedia article exists but it does not directly or clearly answer the user's question; the article may be related or provide partial information."
                "'NoArticleFound' — no relevant Wikipedia article could be found for the query."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The fact or question to check against Wikipedia. Example: 'What is the capital of France?'",
                    },
                },
                "required": ["question"],
                "additionalProperties": False,
            },
        }
        self._system_prompt = "You are an AI assistant that fact-checks information using Wikipedia. Your task is to search for relevant Wikipedia articles and provide accurate answers based on them."
        self._model = model
        self._openai = openai
        self._result = None

    def _clean_up_str(self, raw_str: str) -> str:
        """Strip surrounding code fences and whitespace from model output.

        The model's response is expected to be raw JSON, but may be
        wrapped in Markdown code fences (for example ```json ... ```).
        This helper removes those fences and trims surrounding
        whitespace.

        Args:
            raw_str (str): Raw string returned by the model.

        Returns:
            str: The cleaned JSON string.
        """
        return re.sub(r"(?:^```(?:json)?|```$)", "", raw_str.strip(), flags=re.MULTILINE).strip()

    def _create_answer(self, answer_dict: dict) -> AnswerDict:
        """Convert the structured result into an ``AnswerDict`` for rendering.

        The method maps the internal ``article_answers_question`` status to
        a human-readable message used by the UI.

        Args:
            answer_dict (dict): Parsed JSON result with keys
                ``answer``, ``wikipedia_link``, and ``article_answers_question``.

        Returns:
            AnswerDict: A dictionary containing ``answer_str`` suitable
            for display.
        """
        if answer_dict["article_answers_question"] == "NoArticleFound":
            answer = "No relevant Wikipedia article found to answer the question."
        elif answer_dict["article_answers_question"] == "Inconclusive":
            answer = f"Found a Wikipedia article but it does not conclusively answer the question. \nClosest Answer: {answer_dict['answer']}\nLink: {answer_dict['wikipedia_link']}"
        else:
            answer = f"{answer_dict['answer']}\nSource: {answer_dict['wikipedia_link']}"
        return {"answer_str": answer}

    def run_tool(self, *args: object, **kwargs: object) -> AnswerDict:
        """Query the model/web-search to fact-check a question against Wikipedia.

        This method calls the OpenAI responses API with a web search
        tool, instructing the model to search for a relevant Wikipedia
        article and return a strictly formatted JSON payload. The JSON
        is parsed and converted to an ``AnswerDict`` for display. If
        parsing fails the tool returns an error-like structure encoded
        as an ``AnswerDict``.

        Args:
            question (str): The user's question or claim to verify.

        Returns:
            AnswerDict: A dictionary with an ``answer_str`` that can be
            rendered to the UI.
        """

        # check arguments
        question = kwargs["question"]
        assert isinstance(question, str)

        response = self._openai.responses.create(
            model=self._model,
            tools=[{"type": "web_search"}],
            input=[
                {
                    "role": "user",
                    "content": (
                        f"Search Wikipedia to find information about: '{question}'. "
                        "Find the most relevant Wikipedia article for this question/fact. "
                        "If you find a Wikipedia article, read it and provide an answer to the question based on the article content. "
                        "Return ONLY valid JSON with this exact format:\n\n"
                        "{\n"
                        "  'answer': string,  // The answer to the question based on the Wikipedia article, or null if no article found. This should be a full sentence.\n"
                        "  'wikipedia_link': string,  // The URL link to the Wikipedia article, or null if no article found\n"
                        "  'article_answers_question': string  // One of: 'Yes' (article conclusively answers the question),"
                        "       'Inconclusive' (article exists but doesn't conclusively answer),"
                        "       or 'NoArticleFound' (no Wikipedia article found)\n"
                        "}\n\n"
                        "Do not include commentary. Do not include markdown. Only return valid JSON."
                    ),
                },
            ],
        )

        result_str = get_response_text(response)
        try:
            self._result = json.loads(self._clean_up_str(result_str))
        except json.decoder.JSONDecodeError:
            return {
                "answer_str": "Could not parse response: " + result_str,
            }

        if self._result is None:
            return {
                "answer_str": "No result returned from model.",
            }

        return self._create_answer(self._result)
