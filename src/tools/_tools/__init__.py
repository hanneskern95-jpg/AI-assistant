"""Auto-import all tool modules in the `tools._tools` package.

This package-level initializer iterates over all modules in the
``tools._tools`` directory and imports them. Importing the concrete
tool modules is required because their class definitions use the
``AutoRegister`` metaclass in ``tools.tool``, which appends each
tool class to the central ``registry``. Without this automatic
import, the registry would remain empty.
"""

import importlib
import pkgutil

for module_info in pkgutil.iter_modules(__path__):
    importlib.import_module(f"{__name__}.{module_info.name}")
    