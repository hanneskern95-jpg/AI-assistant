from tool_base import Tool


class ToolLoader:
    """A class responsible for loading tools based on specified groups."""

    def __init__(self, all_available_tools: dict[str, Tool]) -> None:
        """Initialize the ToolLoader with a dictionary of all available tools.

        Args:
            all_available_tools (dict[str, Tool]): A dictionary mapping tool names to their corresponding tool instances.
        """
        self.all_available_tools = all_available_tools

    def load_tools(self, list_of_loaded_groups: list[str]) -> dict[str, Tool]:
        """Load tools based on the specified groups.

        Args:
            list_of_loaded_groups (list[str]): A list of tool groups to load.

        Returns:
            dict[str, Tool]: A dictionary of loaded tools that belong to the specified groups.
        """
        loaded_tools = {}
        for tool_name, tool in self.all_available_tools.items():
            if tool.group in list_of_loaded_groups:
                loaded_tools[tool_name] = tool
        return loaded_tools