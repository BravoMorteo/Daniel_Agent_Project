"""
Core Package
============
Módulos principales del servidor MCP-Odoo: configuración, cliente Odoo y helpers.
"""

from .config import Config
from .odoo_client import OdooClient
from .helpers import encode_content, odoo_form_url, wants_projects, wants_tasks

__all__ = [
    "Config",
    "OdooClient",
    "encode_content",
    "odoo_form_url",
    "wants_projects",
    "wants_tasks",
]
