# tools/users.py
from typing import Optional, List
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    login: str | None = None
    active: bool | None = True

def register(mcp, deps: dict):
    """
    Registra las herramientas MCP relacionadas con Usuarios.
    - list_users: lista usuarios con filtros opcionales.
    """
    odoo = deps["odoo"]

    @mcp.tool(name="list_users", description="Listar usuarios de Odoo con filtros opcionales")
    def list_users(q: Optional[str] = None,
                   active: Optional[bool] = None,
                   limit: int = 50) -> List[User]:
        """
        Lista usuarios (model: res.users).

        Args:
            q: Filtro por nombre (ilike).
            active: True/False para filtrar por estado activo; None = sin filtro.
            limit: Límite de resultados (por defecto 50).

        Returns:
            Lista de User (id, name, login, active).
        """
        domain = []
        if q:
            domain.append(["name", "ilike", q])
        if active is not None:
            domain.append(["active", "=", bool(active)])

        rows = odoo.search_read(
            "res.users",
            domain,
            ["id", "name", "login", "active"],
            limit
        )
        return [User(**row) for row in rows]
