"""Component tests for RecipeSuggestTool."""

import json
from unittest.mock import MagicMock

import pytest

from tools._tools.recipe_creator import RecipeSuggestTool


class TestRecipeSuggestTool:
    """Component tests for the RecipeSuggestTool."""

    @pytest.fixture
    def mock_openai(self) -> MagicMock:
        """Create a mock OpenAI client."""
        mock_client = MagicMock()
        return mock_client

    @pytest.fixture
    def tool(self, mock_openai: MagicMock) -> RecipeSuggestTool:
        """Create a RecipeSuggestTool instance with mocked OpenAI client."""
        return RecipeSuggestTool(model="gpt-4o", openai=mock_openai)

    @pytest.fixture
    def sample_recipes(self) -> list[dict]:
        """Provide sample recipe data for testing."""
        return [
            {
                "title": "Spaghetti Carbonara",
                "link": "https://www.chefkoch.de/rezepte/carbonara",
                "ingredients": ["400g Spaghetti", "200g Guanciale", "4 Eggs", "100g Pecorino Romano"],
                "instructions": ["Boil pasta", "Fry guanciale", "Mix egg and cheese", "Combine all"],
                "description_and_advertisment": "Classic Italian pasta with crispy guanciale and creamy egg sauce.",
            },
            {
                "title": "Margherita Pizza",
                "link": "https://www.chefkoch.de/rezepte/margherita",
                "ingredients": ["500g Flour", "250ml Water", "200g Tomatoes", "250g Mozzarella"],
                "instructions": ["Make dough", "Let rise", "Add toppings", "Bake at 250C"],
                "description_and_advertisment": "Traditional Italian pizza with fresh mozzarella and tomatoes.",
            },
            {
                "title": "Risotto Milanese",
                "link": "https://www.chefkoch.de/rezepte/risotto-milanese",
                "ingredients": ["300g Arborio Rice", "1L Broth", "100g Butter", "50g Saffron"],
                "instructions": ["Heat broth", "Toast rice", "Add broth gradually", "Finish with butter"],
                "description_and_advertisment": "Creamy saffron risotto with rich butter finish.",
            },
        ]

    def test_run_tool_with_valid_recipes(self, tool: RecipeSuggestTool, mock_openai: MagicMock, sample_recipes: list[dict]) -> None:
        """Test run_tool with valid recipe data."""
        mock_response = MagicMock()
        mock_response.output = [
            MagicMock(),  # Index 0 (unused)
            MagicMock(
                content=[
                    MagicMock(
                        text=json.dumps(sample_recipes),
                    ),
                ],
            ),  # Index 1 (used)
        ]
        mock_openai.responses.create.return_value = mock_response

        result = tool.run_tool(description_recipe="Italian pasta dishes")

        assert "answer_str" in result
        assert "recipes" in result
        assert len(result["recipes"]) == 3
        assert result["recipes"][0]["title"] == "Spaghetti Carbonara"
        assert result["recipes"][1]["title"] == "Margherita Pizza"
        assert result["recipes"][2]["title"] == "Risotto Milanese"
        assert "Spaghetti Carbonara" in result["answer_str"]

    def test_run_tool_with_recipes_in_code_fences(self, tool: RecipeSuggestTool, mock_openai: MagicMock, sample_recipes: list[dict]) -> None:
        """Test run_tool handles JSON wrapped in markdown code fences."""
        mock_response = MagicMock()
        mock_response.output = [
            MagicMock(),  # Index 0 (unused)
            MagicMock(
                content=[
                    MagicMock(
                        text=f"```json\n{json.dumps(sample_recipes)}\n```",
                    ),
                ],
            ),  # Index 1 (used)
        ]
        mock_openai.responses.create.return_value = mock_response

        result = tool.run_tool(description_recipe="Italian pasta dishes")

        assert "answer_str" in result
        assert "recipes" in result
        assert len(result["recipes"]) == 3

    def test_run_tool_with_invalid_json(self, tool: RecipeSuggestTool, mock_openai: MagicMock) -> None:
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

        result = tool.run_tool(description_recipe="Italian pasta dishes")

        assert "answer_str" in result
        assert "could not convert the following string into a dictionary" in result["answer_str"]
        assert result["recipes"] == []

    def test_run_tool_calls_openai_with_correct_parameters(self, tool: RecipeSuggestTool, mock_openai: MagicMock, sample_recipes: list[dict]) -> None:
        """Test that run_tool calls the OpenAI API with correct parameters."""
        mock_response = MagicMock()
        mock_response.output = [
            MagicMock(),
            MagicMock(
                content=[
                    MagicMock(
                        text=json.dumps(sample_recipes),
                    ),
                ],
            ),
        ]
        mock_openai.responses.create.return_value = mock_response

        test_description = "Vegan Italian pasta"
        tool.run_tool(description_recipe=test_description)

        # Verify the API was called with correct parameters
        call_args = mock_openai.responses.create.call_args
        assert call_args.kwargs["model"] == "gpt-4o"
        assert call_args.kwargs["tools"] == [{"type": "web_search"}]
        assert call_args.kwargs["input"][0]["role"] == "user"
        assert test_description in call_args.kwargs["input"][0]["content"]
        assert "chefkoch.de" in call_args.kwargs["input"][0]["content"]

    def test_run_tool_with_single_recipe(self, tool: RecipeSuggestTool, mock_openai: MagicMock) -> None:
        """Test run_tool with a single recipe."""
        single_recipe = [{
            "title": "Test Pasta",
            "link": "https://test.com",
            "ingredients": ["Pasta", "Sauce"],
            "instructions": ["Cook pasta", "Add sauce"],
            "description_and_advertisment": "A simple test pasta.",
        }]
        
        mock_response = MagicMock()
        mock_response.output = [
            MagicMock(),
            MagicMock(
                content=[
                    MagicMock(
                        text=json.dumps(single_recipe),
                    ),
                ],
            ),
        ]
        mock_openai.responses.create.return_value = mock_response

        result = tool.run_tool(description_recipe="Simple pasta")

        assert len(result["recipes"]) == 1
        assert result["recipes"][0]["title"] == "Test Pasta"
        assert "Test Pasta" in result["answer_str"]

    def test_run_tool_empty_response_text(self, tool: RecipeSuggestTool, mock_openai: MagicMock) -> None:
        """Test run_tool when response text extraction fails."""
        mock_response = MagicMock()
        mock_response.output = []  # Empty output
        mock_openai.responses.create.return_value = mock_response

        result = tool.run_tool(description_recipe="Italian pasta")

        # When get_response_text fails, it returns empty string which causes JSONDecodeError
        assert "could not convert the following string into a dictionary" in result["answer_str"]
        assert result["recipes"] == []

    def test_create_answer_formats_recipes(self, tool: RecipeSuggestTool, sample_recipes: list) -> None:
        """Test that create_answer properly formats recipes into answer_str."""
        result = tool.create_answer(sample_recipes)

        assert "answer_str" in result
        assert "recipes" in result
        assert len(result["recipes"]) == 3
        assert "Recipe 1: Spaghetti Carbonara" in result["answer_str"]
        assert "Recipe 2: Margherita Pizza" in result["answer_str"]
        assert "Recipe 3: Risotto Milanese" in result["answer_str"]
        assert "Classic Italian pasta" in result["answer_str"]

    def test_is_recipe_type_guard_valid(self, tool: RecipeSuggestTool) -> None:
        """Test that is_recipe correctly validates a valid recipe dict."""
        valid_recipe = {
            "title": "Test",
            "link": "https://test.com",
            "ingredients": ["test"],
            "instructions": ["test"],
            "description_and_advertisment": "test",
        }
        
        assert tool.is_recipe(valid_recipe) is True

    def test_is_recipe_type_guard_missing_field(self, tool: RecipeSuggestTool) -> None:
        """Test that is_recipe rejects dicts with missing required fields."""
        invalid_recipe = {
            "title": "Test",
            "link": "https://test.com",
            "ingredients": ["test"],
            # Missing 'instructions' and 'description_and_advertisment'
        }
        
        assert tool.is_recipe(invalid_recipe) is False

    def test_is_recipe_type_guard_not_dict(self, tool: RecipeSuggestTool) -> None:
        """Test that is_recipe rejects non-dict objects."""
        assert tool.is_recipe("not a dict") is False    # type: ignore
        assert tool.is_recipe(None) is False            # type: ignore
