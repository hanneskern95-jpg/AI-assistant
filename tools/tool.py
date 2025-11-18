

registry = []


class AutoRegister(type):
    def __init__(cls, name, bases, attrs):
        if name != "Tool":
            registry.append(cls)
        super().__init__(name, bases, attrs)


class Tool(metaclass=AutoRegister):

    tool_dict: dict


    def run_tool(self, kwargs) -> str:
        ...
