"""Component tests for WikipediaFactCheckerTool."""

import json
from unittest.mock import MagicMock

import pytest

from tools.wikipedia_fact_checker import WikipediaFactCheckerTool


class TestWikipediaFactCheckerTool:
    """Component tests for the WikipediaFactCheckerTool."""

    @pytest.fixture
    def mock_openai(self) -> MagicMock:
        """Create a mock OpenAI client."""
        mock_client = MagicMock()
        return mock_client

    @pytest.fixture
    def tool(self, mock_openai: MagicMock) -> WikipediaFactCheckerTool:
        """Create a WikipediaFactCheckerTool instance with mocked OpenAI client."""
        return WikipediaFactCheckerTool(model="gpt-4o", openai=mock_openai)

    def test_run_tool_with_conclusive_answer(self, tool: WikipediaFactCheckerTool, mock_openai: MagicMock) -> None:
        """Test run_tool with a conclusive Wikipedia answer."""
        # Mock the response from OpenAI API
        mock_response = MagicMock()
        mock_response.output = [
            MagicMock(),  # Index 0 (unused)
            MagicMock(
                content=[
                    MagicMock(
                        text=json.dumps(
                            {
                                "answer": "The capital of France is Paris.",
                                "wikipedia_link": "https://en.wikipedia.org/wiki/Paris",
                                "article_answers_question": "Yes",
                            }
                        ),
                    ),
                ],
            ),  # Index 1 (used)
        ]
        mock_openai.responses.create.return_value = mock_response

        # Call the run_tool method
        result = tool.run_tool(question="What is the capital of France?")

        # Assertions
        assert "answer_str" in result
        assert "Paris" in result["answer_str"]
        assert "https://en.wikipedia.org/wiki/Paris" in result["answer_str"]
        mock_openai.responses.create.assert_called_once()

    def test_run_tool_with_inconclusive_answer(self, tool: WikipediaFactCheckerTool, mock_openai: MagicMock) -> None:
        """Test run_tool with an inconclusive Wikipedia answer."""
        mock_response = MagicMock()
        mock_response.output = [
            MagicMock(),  # Index 0 (unused)
            MagicMock(
                content=[
                    MagicMock(
                        text=json.dumps(
                            {
                                "answer": "Some partial information found",
                                "wikipedia_link": "https://en.wikipedia.org/wiki/SomeArticle",
                                "article_answers_question": "Inconclusive",
                            }
                        ),
                    ),
                ],
            ),  # Index 1 (used)
        ]
        mock_openai.responses.create.return_value = mock_response

        result = tool.run_tool(question="What is something obscure?")

        assert "answer_str" in result
        assert "does not conclusively answer" in result["answer_str"]
        assert "Some partial information found" in result["answer_str"]

    def test_run_tool_with_no_article_found(self, tool: WikipediaFactCheckerTool, mock_openai: MagicMock) -> None:
        """Test run_tool when no relevant Wikipedia article is found."""
        mock_response = MagicMock()
        mock_response.output = [
            MagicMock(),  # Index 0 (unused)
            MagicMock(
                content=[
                    MagicMock(
                        text=json.dumps(
                            {
                                "answer": None,
                                "wikipedia_link": None,
                                "article_answers_question": "NoArticleFound",
                            }
                        ),
                    ),
                ],
            ),  # Index 1 (used)
        ]
        mock_openai.responses.create.return_value = mock_response

        result = tool.run_tool(question="What is some made-up topic?")

        assert "answer_str" in result
        assert "No relevant Wikipedia article found" in result["answer_str"]

    def test_run_tool_with_json_in_code_fences(self, tool: WikipediaFactCheckerTool, mock_openai: MagicMock) -> None:
        """Test run_tool handles JSON wrapped in markdown code fences."""
        mock_response = MagicMock()
        json_content = {
            "answer": "Test answer",
            "wikipedia_link": "https://example.com",
            "article_answers_question": "Yes",
        }
        mock_response.output = [
            MagicMock(),  # Index 0 (unused)
            MagicMock(
                content=[
                    MagicMock(
                        text=f"```json\n{json.dumps(json_content)}\n```",
                    ),
                ],
            ),  # Index 1 (used)
        ]
        mock_openai.responses.create.return_value = mock_response

        result = tool.run_tool(question="Test question")

        assert "answer_str" in result
        assert "Test answer" in result["answer_str"]

    def test_run_tool_with_invalid_json(self, tool: WikipediaFactCheckerTool, mock_openai: MagicMock) -> None:
        """Test run_tool handles invalid JSON gracefully."""
        mock_response = MagicMock()
        mock_response.output = [
            MagicMock(),  # Index 0 (unused)
            MagicMock(
                content=[
                    MagicMock(
                        text="This is not valid JSON",
                    ),
                ],
            ),  # Index 1 (used)
        ]
        mock_openai.responses.create.return_value = mock_response

        result = tool.run_tool(question="Test question")

        assert "answer_str" in result
        assert "Could not parse response" in result["answer_str"]

    def test_run_tool_calls_openai_with_correct_parameters(self, tool: WikipediaFactCheckerTool, mock_openai: MagicMock) -> None:
        """Test that run_tool calls the OpenAI API with correct parameters."""
        mock_response = MagicMock()
        mock_response.output = [
            MagicMock(),
            MagicMock(
                content=[
                    MagicMock(
                        text=json.dumps(
                            {
                                "answer": "Test",
                                "wikipedia_link": "https://test.com",
                                "article_answers_question": "Yes",
                            }
                        ),
                    ),
                ],
            ),
        ]
        mock_openai.responses.create.return_value = mock_response

        test_question = "Is Python a programming language?"
        tool.run_tool(question=test_question)

        # Verify the API was called with correct parameters
        call_args = mock_openai.responses.create.call_args
        assert call_args.kwargs["model"] == "gpt-4o"
        assert call_args.kwargs["tools"] == [{"type": "web_search"}]
        assert call_args.kwargs["input"][0]["role"] == "user"
        assert test_question in call_args.kwargs["input"][0]["content"]
