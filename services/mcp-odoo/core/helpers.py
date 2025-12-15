"""
Helpers Module
==============
Funciones de utilidad compartidas para el servidor MCP-Odoo.
"""

import json
from typing import Dict, Any


def encode_content(obj: Any) -> Dict[str, Any]:
    """
    Envuelve un objeto en el formato de content array de MCP.

    Args:
        obj: Objeto a envolver (será serializado como JSON)

    Returns:
        Dict con estructura: {"content": [{"type": "text", "text": "..."}]}
    """
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(obj, ensure_ascii=False),
            }
        ]
    }


def odoo_form_url(model: str, rec_id: int, base_url: str = None) -> str:
    """
    Genera URL del formulario de Odoo para un registro.

    Args:
        model: Nombre del modelo Odoo (ej: "project.project")
        rec_id: ID del registro
        base_url: URL base de Odoo (si None, usa variable de entorno)

    Returns:
        URL del formulario
    """
    if not base_url:
        from .config import Config

        base_url = Config.ODOO_URL

    if not base_url:
        return f"odoo://{model}/{rec_id}"

    base_url = base_url.rstrip("/")
    return f"{base_url}/web#id={rec_id}&model={model}&view_type=form"


def wants_projects(query: str) -> bool:
    """
    Detecta si la query busca proyectos.

    Args:
        query: Texto de búsqueda

    Returns:
        True si la query menciona proyectos
    """
    ql = query.lower()
    return any(t in ql for t in ("proyecto", "proyectos", "project", "projects"))


def wants_tasks(query: str) -> bool:
    """
    Detecta si la query busca tareas.

    Args:
        query: Texto de búsqueda

    Returns:
        True si la query menciona tareas
    """
    ql = query.lower()
    return any(t in ql for t in ("tarea", "tareas", "task", "tasks"))
