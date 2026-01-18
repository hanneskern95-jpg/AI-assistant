"""Component tests for the create_tools function."""

from unittest.mock import MagicMock, patch
import pytest

from src.tools.create import create_tools, _get_attributes, _get_subkwargs
from src.tools.tool import Tool, AnswerDict


class MockToolA(Tool):
    """Mock tool class A for testing."""

    def __init__(self, model: str, openai):
        """Initialize MockToolA."""
        self.tool_dict = {
            "type": "function",
            "name": "mock_tool_a",
            "description": "Mock tool A for testing",
            "parameters": {},
        }
        self.model = model
        self.openai = openai

    def run_tool(self, **kwargs) -> AnswerDict:
        """Run the mock tool."""
        return {"answer_str": "Mock A executed"}


class MockToolB(Tool):
    """Mock tool class B for testing."""

    def __init__(self, model: str):
        """Initialize MockToolB."""
        self.tool_dict = {
            "type": "function",
            "name": "mock_tool_b",
            "description": "Mock tool B for testing",
            "parameters": {},
        }
        self.model = model

    def run_tool(self, **kwargs) -> AnswerDict:
        """Run the mock tool."""
        return {"answer_str": "Mock B executed"}


class MockToolC(Tool):
    """Mock tool class C for testing."""

    def __init__(self, openai):
        """Initialize MockToolC."""
        self.tool_dict = {
            "type": "function",
            "name": "mock_tool_c",
            "description": "Mock tool C for testing",
            "parameters": {},
        }
        self.openai = openai

    def run_tool(self, **kwargs) -> AnswerDict:
        """Run the mock tool."""
        return {"answer_str": "Mock C executed"}


class TestCreateTools:
    """Component tests for the create_tools function."""

    @pytest.fixture
    def mock_openai(self):
        """Create a mock OpenAI client."""
        return MagicMock()

    def test_get_subkwargs_extracts_requested_keys(self):
        """Test that _get_subkwargs extracts only requested keys."""
        kwargs = {"model": "gpt-4o", "openai": "client", "extra": "ignored"}
        keys = ["model", "openai"]

        result = _get_subkwargs(kwargs, keys)

        assert result == {"model": "gpt-4o", "openai": "client"}

    def test_get_subkwargs_with_all_keys_present(self):
        """Test _get_subkwargs when all requested keys are present."""
        kwargs = {"a": 1, "b": 2, "c": 3}
        keys = ["a", "b", "c"]

        result = _get_subkwargs(kwargs, keys)

        assert result == {"a": 1, "b": 2, "c": 3}

    def test_get_subkwargs_raises_key_error_for_missing_key(self):
        """Test that _get_subkwargs raises KeyError for missing keys."""
        kwargs = {"model": "gpt-4o"}
        keys = ["model", "openai"]

        with pytest.raises(KeyError):
            _get_subkwargs(kwargs, keys)

    def test_get_attributes_returns_constructor_parameters(self):
        """Test that _get_attributes returns constructor parameter names."""
        attributes = _get_attributes(MockToolA)

        assert "model" in attributes
        assert "openai" in attributes
        assert "self" not in attributes

    def test_get_attributes_returns_single_parameter(self):
        """Test _get_attributes with a tool that has one parameter."""
        attributes = _get_attributes(MockToolB)

        assert attributes == ["model"]

    def test_get_attributes_returns_correct_count(self):
        """Test _get_attributes returns correct number of parameters."""
        attributes_a = _get_attributes(MockToolA)
        attributes_b = _get_attributes(MockToolB)
        attributes_c = _get_attributes(MockToolC)

        assert len(attributes_a) == 2
        assert len(attributes_b) == 1
        assert len(attributes_c) == 1

    def test_registry_contains_mock_tools(self):
        """Test that the registry contains the mock tool classes."""
        with patch("src.tools.create.registry", [MockToolA, MockToolB, MockToolC]):
            from src.tools.create import registry

            assert MockToolA in registry
            assert MockToolB in registry
            assert MockToolC in registry

    @patch("src.tools.create.registry", [MockToolA, MockToolB, MockToolC])
    def test_create_tools_initializes_all_tools(self, mock_openai):
        """Test that create_tools initializes all tools in the registry."""
        tools = create_tools(model="gpt-4o", openai=mock_openai)

        assert len(tools) == 3
        assert "mock_tool_a" in tools
        assert "mock_tool_b" in tools
        assert "mock_tool_c" in tools

    @patch("src.tools.create.registry", [MockToolA, MockToolB, MockToolC])
    def test_create_tools_returns_tool_instances(self, mock_openai):
        """Test that create_tools returns instances of the correct types."""
        tools = create_tools(model="gpt-4o", openai=mock_openai)

        assert isinstance(tools["mock_tool_a"], MockToolA)
        assert isinstance(tools["mock_tool_b"], MockToolB)
        assert isinstance(tools["mock_tool_c"], MockToolC)

    @patch("src.tools.create.registry", [MockToolA, MockToolB, MockToolC])
    def test_create_tools_passes_correct_kwargs_to_each_tool(self, mock_openai):
        """Test that each tool receives only the kwargs it needs."""
        tools = create_tools(model="gpt-4o", openai=mock_openai, extra_param="ignored")

        # MockToolA requires model and openai
        assert tools["mock_tool_a"].model == "gpt-4o"
        assert tools["mock_tool_a"].openai == mock_openai

        # MockToolB requires only model
        assert tools["mock_tool_b"].model == "gpt-4o"
        assert not hasattr(tools["mock_tool_b"], "openai")

        # MockToolC requires only openai
        assert tools["mock_tool_c"].openai == mock_openai
        assert not hasattr(tools["mock_tool_c"], "model")

    def test_create_tools_with_empty_registry(self):
        """Test create_tools with an empty registry."""
        with patch("src.tools.create.registry", []):
            tools = create_tools(model="gpt-4o")

        assert tools == {}

    @patch("src.tools.create.registry", [MockToolA, MockToolB])
    def test_create_tools_with_partial_kwargs(self, mock_openai):
        """Test create_tools when only some tools receive their required kwargs. In this case, we expect it to throw a KeyError"""
        # MockToolA should raise KeyError (needs openai which is not provided)
        with pytest.raises(KeyError):
            create_tools(model="gpt-4o")

    @patch("src.tools.create.registry", [MockToolA, MockToolB, MockToolC])
    def test_create_tools_can_run_tools(self, mock_openai):
        """Test that created tools can be executed."""
        tools = create_tools(model="gpt-4o", openai=mock_openai)

        result_a = tools["mock_tool_a"].run_tool()
        result_b = tools["mock_tool_b"].run_tool()
        result_c = tools["mock_tool_c"].run_tool()

        assert result_a["answer_str"] == "Mock A executed"
        assert result_b["answer_str"] == "Mock B executed"
        assert result_c["answer_str"] == "Mock C executed"

    @patch("src.tools.create.registry", [MockToolA, MockToolB, MockToolC])
    def test_create_tools_with_extra_kwargs(self, mock_openai):
        """Test that create_tools ignores extra kwargs not used by any tool."""
        tools = create_tools(
            model="gpt-4o",
            openai=mock_openai,
            unused_param1="value1",
            unused_param2="value2"
        )

        # All tools should still be created successfully
        assert len(tools) == 3
        assert all(tool_name in tools for tool_name in ["mock_tool_a", "mock_tool_b", "mock_tool_c"])
