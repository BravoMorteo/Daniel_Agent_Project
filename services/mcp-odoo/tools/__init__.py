"""Autoload de módulos de tools.

Cada módulo debe exponer una función:
    register(mcp: FastMCP, deps: dict) -> None
    o
    register_<nombre>_tools(mcp: FastMCP, deps: dict) -> None

donde `deps` puede contener clientes compartidos (p.ej. {'odoo': OdooClient}).
"""

import importlib
import pkgutil
from types import ModuleType


def load_all(mcp, deps: dict, package_name: str = __name__):
    package = importlib.import_module(package_name)
    for info in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
        mod = importlib.import_module(info.name)
        _register_from_module(mod, mcp, deps)


def _register_from_module(mod: ModuleType, mcp, deps: dict):
    # Intentar función 'register' estándar
    reg = getattr(mod, "register", None)
    if callable(reg):
        reg(mcp, deps)
        return

    # Intentar función 'register_<nombre>_tools'
    module_name = mod.__name__.split(".")[-1]
    reg_alt = getattr(mod, f"register_{module_name}_tools", None)
    if callable(reg_alt):
        reg_alt(mcp, deps)
