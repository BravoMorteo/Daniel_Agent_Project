from typing import Optional, List
from pydantic import BaseModel

class Project(BaseModel):
    id: int
    name: str
    active: bool | None = True

def register(mcp, deps: dict):
    """
    Registra las herramientas MCP relacionadas con Proyectos.
    - list_projects: lista proyectos con filtros opcionales.
    """
    odoo = deps["odoo"]

    @mcp.tool(name="list_projects", description="Listar proyectos de Odoo con filtros opcionales")
    def list_projects(q: Optional[str] = None,
                      active: Optional[bool] = None,
                      limit: int = 50) -> List[Project]:
        """
        Lista proyectos (model: project.project).

        Args:
            q: Filtro por nombre (ilike).
            active: True/False para filtrar por estado activo; None = sin filtro.
            limit: Límite de resultados (por defecto 50).

        Returns:
            Lista de Project (id, name, active).
        """
        domain = []
        if q:
            domain.append(["name", "ilike", q])
        if active is not None:
            domain.append(["active", "=", bool(active)])

        rows = odoo.search_read(
            "project.project",
            domain,
            ["id", "name", "active"],
            limit
        )
        return [Project(**row) for row in rows]
