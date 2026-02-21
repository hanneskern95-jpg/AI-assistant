from tool_base.tool_base import Tool
from tool_loader.loader import ToolLoader


class DummyTool(Tool):
    def __init__(self, group: str) -> None:
        self.group = group

    def run(self) -> str:
        return f"Running tool in group {self.group}"

def test_load_tools_returns_correct_tools() -> None:
    tool_a = DummyTool(group="group1")
    tool_b = DummyTool(group="group2")
    tool_c = DummyTool(group="group1")
    all_tools = {
        "tool_a": tool_a,
        "tool_b": tool_b,
        "tool_c": tool_c,
    }
    loader = ToolLoader(all_tools) # type: ignore
    loaded = loader.load_tools(["group1"])
    assert "tool_a" in loaded
    assert "tool_c" in loaded
    assert "tool_b" not in loaded
    assert loaded["tool_a"].group == "group1"
    assert loaded["tool_c"].group == "group1"

def test_load_tools_empty_group() -> None:
    tool_a = DummyTool(group="group1")
    all_tools = {"tool_a": tool_a}
    loader = ToolLoader(all_tools) # type: ignore
    loaded = loader.load_tools(["group2"])
    assert loaded == {}

def test_load_tools_multiple_groups() -> None:
    tool_a = DummyTool(group="group1")
    tool_b = DummyTool(group="group2")
    tool_c = DummyTool(group="group3")
    all_tools = {
        "tool_a": tool_a,
        "tool_b": tool_b,
        "tool_c": tool_c,
    }
    loader = ToolLoader(all_tools) # type: ignore
    loaded = loader.load_tools(["group1", "group3"])
    assert "tool_a" in loaded
    assert "tool_c" in loaded
    assert "tool_b" not in loaded
