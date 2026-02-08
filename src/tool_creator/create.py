"""Create and initialize tool instances from the `_tools` package.

This module provides helpers to build a dictionary of tool instances
based on the `registry` exported by ``tool_base.tool_base``. Each entry in the
registry is a tool class; ``create_tools`` inspects the constructor
parameters of each tool class and initializes it using a filtered set
of keyword arguments supplied by the caller.

Typical usage::

    tools = create_tools(model="gpt-4o-mini", openai=openai_client)

The function will only pass constructor parameters that the tool
class declares, ignoring any extra keys in the provided kwargs.
"""

import inspect
from typing import Any

from tool_base import Tool, registry  # registry is filled after _tools is imported
import tools  # noqa: F401 Import all tool modules to populate the registry


def _get_subkwargs(kwargs: dict, keys: list[str]) -> dict:
    """Return a dictionary containing only selected keys from ``kwargs``.

    This helper picks the provided ``keys`` out of ``kwargs`` and
    returns a new dict suitable for passing to a tool constructor.

    Args:
        kwargs (dict): The source keyword arguments.
        keys (list[str]): The keys to extract from ``kwargs``.

    Returns:
        dict: A new dictionary containing only the requested keys and
        their values. If a key is missing in ``kwargs`` a ``KeyError``
        will propagate from the lookup (caller responsibility).
    """
    return {key: kwargs[key] for key in keys}


def _get_attributes(class_to_inspect: type[Tool]) -> list[Any]:
    """Return the constructor parameter names for the given tool class.

    Uses ``inspect.signature`` to obtain the parameter names declared
    on the tool class' ``__init__``. The returned list can be used to
    filter a superset of kwargs down to the subset accepted by the
    constructor.

    Args:
        class_to_inspect (type[Tool]): The tool class to inspect.

    Returns:
        list[Any]: A list of parameter names (as strings) accepted by the
        tool class constructor.
    """
    return list(inspect.signature(class_to_inspect).parameters)


def create_tools(**kwargs: object) -> dict[str, Tool]:
    """Instantiate all tools registered in ``tools.tool.registry``.

    For each tool class in the central registry this function determines
    which of the provided ``kwargs`` apply to that class' constructor,
    instantiates the class with the filtered arguments, and returns a
    mapping from tool name to the initialized tool instance.

    Args:
        **kwargs: Arbitrary keyword arguments that may be required by
            one or more tool constructors (for example ``model`` or
            ``openai``). Only parameters matching a given tool's
            constructor are forwarded to that tool.

    Returns:
        dict[str, Tool]: A dictionary mapping each tool's declared name
        (``tool.tool_dict['name']``) to the initialized ``Tool``
        instance.
    """
    initialized_objects: dict[str, Tool] = {}
    for cls in registry:
        keys = _get_attributes(cls)
        filtered_kwargs = _get_subkwargs(kwargs=kwargs, keys=keys)
        obj = cls(**filtered_kwargs)
        initialized_objects[obj.tool_dict["name"]] = obj
    return initialized_objects
