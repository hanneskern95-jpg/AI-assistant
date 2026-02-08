"""Tools package for the ChatAssistant.

This package contains tools that the ChatAssistant automatically includes
when running. The automatic inclusion and registration of tools is handled
by the tool_creator package.

All tools in this package are subclasses of the ``Tool`` class, which is
found in the ``tool_base`` package.

Package-level initializer:
This package-level initializer iterates over all modules in the
``tools`` directory and imports them. Importing the concrete
tool modules is required because their class definitions use the
``AutoRegister`` metaclass in ``tool_base.tool_base``, which appends each
tool class to the central ``registry``. Without this automatic
import, the registry would remain empty.
"""

import importlib
import pkgutil

for module_info in pkgutil.iter_modules(__path__):
    importlib.import_module(f"{__name__}.{module_info.name}")
