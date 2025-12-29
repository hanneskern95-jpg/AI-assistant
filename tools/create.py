import inspect
from typing import Any

from .tool import Tool, registry  # registry is filled after _tools is imported


def _get_subkwargs(kwargs: dict, keys: list[str]) -> dict:
    return {key:kwargs[key] for key in keys}


def _get_attributes(class_to_inspect: type[Tool]) -> list[Any]:
    return list(inspect.signature(class_to_inspect).parameters)


def create_tools(**kwargs: dict) -> dict[str, Tool]:
    initialized_objects = {}
    for cls in registry:
        keys = _get_attributes(cls)
        filtered_kwargs = _get_subkwargs(kwargs=kwargs, keys=keys)
        obj = cls(**filtered_kwargs)
        initialized_objects[obj.tool_dict["name"]] = obj
    return initialized_objects
