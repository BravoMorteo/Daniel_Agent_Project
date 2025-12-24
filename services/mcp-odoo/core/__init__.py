"""
Core Package
============
Módulos principales del servidor MCP-Odoo: configuración, cliente Odoo, helpers,
gestión de tareas asíncronas, API FastAPI y logging.
"""

from .config import Config
from .odoo_client import OdooClient
from .helpers import encode_content, odoo_form_url, wants_projects, wants_tasks
from .tasks import TaskManager, QuotationTask, TaskStatus, task_manager
from .api import api_app
from .logger import QuotationLogger, quotation_logger

__all__ = [
    "Config",
    "OdooClient",
    "encode_content",
    "odoo_form_url",
    "wants_projects",
    "wants_tasks",
    "TaskManager",
    "QuotationTask",
    "TaskStatus",
    "task_manager",
    "api_app",
    "QuotationLogger",
    "quotation_logger",
]
