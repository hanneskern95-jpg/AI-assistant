"""Component tests for the Assistant class."""

import json
from unittest.mock import MagicMock, patch

from openai import OpenAI
from openai.types.chat import ChatCompletionMessage
from openai.types.chat.chat_completion_message_function_tool_call import ChatCompletionMessageFunctionToolCall
import pytest

from src.chat_assistant import Assistant
from src.tools.tool import AnswerDict, Tool


class MockTool1(Tool):
    """Mock tool class 1 for testing."""

    def __init__(self, model: str, openai: OpenAI) -> None:
        """Initialize MockTool1."""
        self.tool_dict = {
            "type": "function",
            "name": "mock_tool_1",
            "description": "Mock tool 1 for testing",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A query string",
                    },
                },
                "required": ["query"],
            },
        }
        self.model = model
        self.openai = openai
        self.last_query = None

    def run_tool(self, *args: object, **kwargs: object) -> AnswerDict:
        """Run the mock tool."""
        self.last_query = kwargs["query"]
        return {"answer_str": f"Mock tool 1 result for: {self.last_query}"}

    def render_answer(self, answer: AnswerDict) -> None:
        """Render answer (mock implementation)."""
        pass

    def render_pinned_object(self, answer: dict) -> None:
        """Render pinned object (mock implementation)."""
        pass


class MockTool2(Tool):
    """Mock tool class 2 for testing."""

    def __init__(self, model: str, openai: OpenAI) -> None:
        """Initialize MockTool2."""
        self.tool_dict = {
            "type": "function",
            "name": "mock_tool_2",
            "description": "Mock tool 2 for testing",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "A topic string",
                    },
                },
                "required": ["topic"],
            },
        }
        self.model = model
        self.openai = openai
        self.last_topic = None

    def run_tool(self, *args: object, **kwargs: object) -> AnswerDict:
        """Run the mock tool."""
        self.last_topic = kwargs["topic"]
        return {"answer_str": f"Mock tool 2 result for: {self.last_topic}"}

    def render_answer(self, answer: AnswerDict) -> None:
        """Render answer (mock implementation)."""
        pass

    def render_pinned_object(self, answer: dict) -> None:
        """Render pinned object (mock implementation)."""
        pass


class TestAssistant:
    """Component tests for the Assistant class."""

    @pytest.fixture
    def mock_tools(self) -> dict[str, Tool]:
        """Provide mock tools for testing."""
        return {}

    @pytest.fixture
    def assistant(self) -> Assistant:
        """Create an Assistant instance with mocked dependencies."""
        with patch("src.chat_assistant.create_tools") as mock_create_tools:
            mock_tool_1 = MockTool1(model="gpt-4o-mini", openai=MagicMock())
            mock_tool_2 = MockTool2(model="gpt-4o-mini", openai=MagicMock())
            mock_create_tools.return_value = {
                "mock_tool_1": mock_tool_1,
                "mock_tool_2": mock_tool_2,
            }
            
            with patch("src.chat_assistant.load_dotenv"):
                with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
                    assistant = Assistant()
        
        return assistant

    def test_assistant_initialization(self, assistant: Assistant) -> None:
        """Test that Assistant is initialized with correct attributes."""
        assert assistant.system_message == "You are an AI assistant."
        assert assistant.tools is not None
        assert len(assistant.tools) == 2
        assert "mock_tool_1" in assistant.tools
        assert "mock_tool_2" in assistant.tools
        assert assistant.history == []

    def test_assistant_tool_dicts_format(self, assistant: Assistant) -> None:
        """Test that tool_dicts are properly formatted."""
        tool_dicts = assistant.tool_dicts
        
        assert len(tool_dicts) == 2
        for tool_dict in tool_dicts:
            assert tool_dict["type"] == "function"
            assert "function" in tool_dict
            assert tool_dict["function"]["type"] == "function"
            assert tool_dict["function"]["name"] in ["mock_tool_1", "mock_tool_2"]

    def test_get_attributes_from_tool_call_message_valid_call(self, assistant: Assistant) -> None:
        """Test extracting attributes from a valid tool call message."""
        # Create a mock tool call message
        mock_function = MagicMock()
        mock_function.name = "mock_tool_1"
        mock_function.arguments = json.dumps({"query": "test query"})
        
        mock_tool_call = MagicMock(spec=ChatCompletionMessageFunctionToolCall)
        mock_tool_call.id = "call_123"
        mock_tool_call.type = "function"
        mock_tool_call.function = mock_function
        
        mock_message = MagicMock(spec=ChatCompletionMessage)
        mock_message.tool_calls = [mock_tool_call]
        
        tool_call, func_name, args, args_str = assistant.get_attributes_from_tool_call_message(mock_message)
        
        assert tool_call == mock_tool_call
        assert func_name == "mock_tool_1"
        assert args == {"query": "test query"}
        assert args_str == json.dumps({"query": "test query"})

    def test_get_attributes_from_tool_call_message_no_calls(self, assistant: Assistant) -> None:
        """Test extracting attributes when no tool calls present."""
        mock_message = MagicMock(spec=ChatCompletionMessage)
        mock_message.tool_calls = None
        
        with patch("streamlit.error"):
            tool_call, func_name, args, args_str = assistant.get_attributes_from_tool_call_message(mock_message)
        
        assert tool_call is None
        assert func_name == ""
        assert args == {}
        assert args_str == ""

    def test_get_attributes_from_tool_call_message_no_function(self, assistant: Assistant) -> None:
        """Test extracting attributes when function attribute is missing."""
        mock_tool_call = MagicMock()
        mock_tool_call.function = None
        
        mock_message = MagicMock(spec=ChatCompletionMessage)
        mock_message.tool_calls = [mock_tool_call]
        
        with patch("streamlit.error"):
            tool_call, func_name, args, args_str = assistant.get_attributes_from_tool_call_message(mock_message)
        
        assert tool_call is None
        assert func_name == ""
        assert args == {}
        assert args_str == ""

    def test_handle_tools_executes_tool(self, assistant: Assistant) -> None:
        """Test that handle_tools executes the correct tool."""
        # Create a mock tool call message
        mock_function = MagicMock()
        mock_function.name = "mock_tool_1"
        mock_function.arguments = json.dumps({"query": "test query"})
        
        mock_tool_call = MagicMock(spec=ChatCompletionMessageFunctionToolCall)
        mock_tool_call.id = "call_123"
        mock_tool_call.type = "function"
        mock_tool_call.function = mock_function
        
        mock_message = MagicMock(spec=ChatCompletionMessage)
        mock_message.tool_calls = [mock_tool_call]
        
        with patch("streamlit.error"):
            result = assistant.handle_tools(mock_message)
        
        # Tool should have been executed
        assert assistant.tools["mock_tool_1"].last_query == "test query" # type: ignore
        assert "Mock tool 1 result for: test query" == result["answer_str"]

    def test_handle_tools_appends_to_history(self, assistant: Assistant) -> None:
        """Test that handle_tools appends messages to history."""
        initial_history_length = len(assistant.history)
        
        # Create a mock tool call message
        mock_function = MagicMock()
        mock_function.name = "mock_tool_1"
        mock_function.arguments = json.dumps({"query": "test"})
        
        mock_tool_call = MagicMock(spec=ChatCompletionMessageFunctionToolCall)
        mock_tool_call.id = "call_123"
        mock_tool_call.type = "function"
        mock_tool_call.function = mock_function
        
        mock_message = MagicMock(spec=ChatCompletionMessage)
        mock_message.tool_calls = [mock_tool_call]
        
        with patch("streamlit.error"):
            assistant.handle_tools(mock_message)
        
        # Should have added assistant message and tool response
        assert len(assistant.history) == initial_history_length + 2
        assert assistant.history[-2]["role"] == "assistant"
        assert assistant.history[-1]["role"] == "tool"

    def test_handle_tools_with_no_tool_call(self, assistant: Assistant) -> None:
        """Test handle_tools when no tool call is present."""
        mock_message = MagicMock(spec=ChatCompletionMessage)
        mock_message.tool_calls = None
        
        with patch("streamlit.error"):
            result = assistant.handle_tools(mock_message)
        
        assert "Error: No tool call found" in result["answer_str"]

    def test_chat_with_tool_appends_user_message(self, assistant: Assistant) -> None:
        """Test that chat_with_tool appends user message to history."""
        initial_history_length = len(assistant.history)
        
        with patch.object(assistant.openai.chat.completions, "create") as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(
                finish_reason="stop",
                message=MagicMock(content="Assistant response"),
            )]
            mock_create.return_value = mock_response
            
            assistant.chat_with_tool("Hello assistant") # type: ignore
        
        assert len(assistant.history) > initial_history_length
        assert assistant.history[0]["role"] == "user"
        assert assistant.history[0]["content"] == "Hello assistant"

    def test_chat_with_tool_calls_openai_with_system_message(self, assistant: Assistant) -> None:
        """Test that chat_with_tool calls openai with the correct parameters."""
        with patch.object(assistant.openai.chat.completions, "create") as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(
                finish_reason="stop",
                message=MagicMock(content="Response"),
            )]
            mock_create.return_value = mock_response
            
            assistant.chat_with_tool("Test message") # type: ignore
            
            call_args = mock_create.call_args
            messages = call_args.kwargs["messages"]
            assert messages[0]["role"] == "system"
            assert messages[0]["content"] == "You are an AI assistant."
            assert messages[1]["role"] == "user"
            assert "Test message" == messages[1]["content"]

    def test_chat_with_tool_handles_tool_call_response(self, assistant: Assistant) -> None:
        """Test that chat_with_tool handles tool call responses."""
        mock_function = MagicMock()
        mock_function.name = "mock_tool_1"
        mock_function.arguments = json.dumps({"query": "test"})
        
        mock_tool_call = MagicMock(spec=ChatCompletionMessageFunctionToolCall)
        mock_tool_call.id = "call_123"
        mock_tool_call.type = "function"
        mock_tool_call.function = mock_function
        
        with patch.object(assistant.openai.chat.completions, "create") as mock_create:
            mock_response = MagicMock()
            mock_message = MagicMock(spec=ChatCompletionMessage)
            mock_message.tool_calls = [mock_tool_call]
            mock_response.choices = [MagicMock(
                finish_reason="tool_calls",
                message=mock_message,
            )]
            mock_create.return_value = mock_response
            
            with patch("streamlit.error"):
                assistant.chat_with_tool("Execute tool") # type: ignore
        
        # Should have appended tool-related messages
        tool_messages = [msg for msg in assistant.history if msg["role"] == "tool"]
        assert len(tool_messages) > 0

    def test_chat_with_tool_appends_assistant_response(self, assistant: Assistant) -> None:
        """Test that chat_with_tool appends assistant response for non-tool messages."""
        with patch.object(assistant.openai.chat.completions, "create") as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(
                finish_reason="stop",
                message=MagicMock(content="Hello user!"),
            )]
            mock_create.return_value = mock_response
            
            assistant.chat_with_tool("Test message") # type: ignore
            
            # Should have user and assistant messages
            assistant_messages = [msg for msg in assistant.history if msg["role"] == "assistant"]
            assert len(assistant_messages) > 0
            assert assistant_messages[-1]["content"] == "Hello user!"

    def test_assistant_maintains_history(self, assistant: Assistant) -> None:
        """Test that assistant maintains conversation history."""
        with patch.object(assistant.openai.chat.completions, "create") as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(
                finish_reason="stop",
                message=MagicMock(content="Response 1"),
            )]
            mock_create.return_value = mock_response
            
            assistant.chat_with_tool("Message 1") # type: ignore
            assert len(assistant.history) == 2  # user + assistant
            
            assistant.chat_with_tool("Message 2") # type: ignore
            assert len(assistant.history) == 4  # 2 + user + assistant

    def test_handle_tools_stores_correct_tool_call_id(self, assistant: Assistant) -> None:
        """Test that handle_tools stores the correct tool call ID."""
        mock_function = MagicMock()
        mock_function.name = "mock_tool_1"
        mock_function.arguments = json.dumps({"query": "test"})
        
        mock_tool_call = MagicMock(spec=ChatCompletionMessageFunctionToolCall)
        mock_tool_call.id = "call_xyz_789"
        mock_tool_call.type = "function"
        mock_tool_call.function = mock_function
        
        mock_message = MagicMock(spec=ChatCompletionMessage)
        mock_message.tool_calls = [mock_tool_call]
        
        with patch("streamlit.error"):
            assistant.handle_tools(mock_message)
        
        # Find the tool response in history
        tool_response = next(msg for msg in assistant.history if msg["role"] == "tool")
        assert tool_response["tool_call_id"] == "call_xyz_789"
