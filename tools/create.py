from .tool import registry   # registry is filled after _tools is imported
import inspect


def get_subkwargs(kwargs: dict, keys: list[str]):
    return {key:kwargs[key] for key in keys}


def get_attributes(class_to_inspect):
    return [key for key in inspect.signature(class_to_inspect).parameters]


def create_tools(**kwargs):
    initialized_objects = {}
    for cls in registry:
        keys = get_attributes(cls)
        filtered_kwargs = get_subkwargs(kwargs=kwargs, keys=keys)
        object = cls(**filtered_kwargs)
        initialized_objects[object.tool_dict["name"]] = object
    return initialized_objects
