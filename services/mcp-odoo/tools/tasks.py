# tools/tasks.py
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, field_validator

class Task(BaseModel):
    id: int
    name: str
    project_id: Any
    assignees: List[Any] = []
    stage_id: Any
    date_deadline: Optional[str] = None

    @field_validator("date_deadline", mode="before")
    def _normalize_deadline(cls, v):
        if v is False or v is None or v == "":
            return None
        return str(v)

def register(mcp, deps: dict):
    """
    Herramientas MCP para Tareas (project.task).
    - list_tasks: permite filtrar por id de proyecto, usuario, etapa o nombre de usuario.
    - get_task: obtiene detalles de una tarea por id.
    """
    odoo = deps["odoo"]

    def _detect_user_field() -> Dict[str, str]:
        fields = odoo.execute_kw("project.task", "fields_get", [], {"attributes": ["type"]})
        if "user_id" in fields:
            return {"field": "user_id", "mode": "single"}
        return {"field": "user_ids", "mode": "multi"}

    def _assignees_from_row(row: Dict[str, Any], user_field: str) -> List[Any]:
        val = row.get(user_field)
        if not val:
            return []
        if user_field == "user_id":
            return [val] if isinstance(val, list) else []
        if isinstance(val, list):
            if len(val) >= 1 and isinstance(val[0], int):
                return [val]
            return val
        return []

    @mcp.tool(
        name="list_tasks",
        description="Listar tareas (project.task) con filtros opcionales; incluye búsqueda por nombre de usuario"
    )
    def list_tasks(project_id: Optional[int] = None,
                   assigned_to: Optional[int] = None,
                   assigned_to_name: Optional[str] = None,
                   stage_id: Optional[int] = None,
                   q: Optional[str] = None,
                   limit: int = 50) -> List[Task]:
        user_info = _detect_user_field()
        user_field = user_info["field"]
        is_single = user_info["mode"] == "single"

        domain = []

        if project_id:
            domain.append(["project_id", "=", int(project_id)])

        # --- Nuevo: buscar por nombre de usuario ---
        if assigned_to_name and not assigned_to:
            users = odoo.search_read("res.users", [["name", "ilike", assigned_to_name]], ["id"], 1)
            if users:
                assigned_to = users[0]["id"]

        if assigned_to:
            if is_single:
                domain.append([user_field, "=", int(assigned_to)])
            else:
                domain.append([user_field, "in", [int(assigned_to)]])

        if stage_id:
            domain.append(["stage_id", "=", int(stage_id)])
        if q:
            domain.append(["name", "ilike", q])

        fields = ["id", "name", "project_id", "stage_id", "date_deadline", user_field]
        rows = odoo.search_read("project.task", domain, fields, limit)

        tasks: List[Task] = []
        for r in rows:
            payload = {
                "id": r["id"],
                "name": r.get("name") or "",
                "project_id": r.get("project_id"),
                "stage_id": r.get("stage_id"),
                "date_deadline": r.get("date_deadline"),
                "assignees": _assignees_from_row(r, user_field),
            }
            tasks.append(Task.model_validate(payload))
        return tasks

    @mcp.tool(
        name="get_task",
        description="Obtener detalle de una tarea por id; compatibilidad user_id/user_ids."
    )
    def get_task(task_id: int, include_description: bool = True) -> Dict[str, Any]:
        user_info = _detect_user_field()
        user_field = user_info["field"]

        fields = ["id", "name", "project_id", "stage_id", "date_deadline", user_field]
        if include_description:
            fields.append("description")

        rows = odoo.search_read("project.task", [["id", "=", int(task_id)]], fields, 1)
        if not rows:
            return {"error": f"Task {task_id} not found"}
        r = rows[0]

        doc = Task.model_validate({
            "id": r["id"],
            "name": r.get("name") or "",
            "project_id": r.get("project_id"),
            "stage_id": r.get("stage_id"),
            "date_deadline": r.get("date_deadline"),
            "assignees": _assignees_from_row(r, user_field),
        }).model_dump()

        if include_description:
            doc["description"] = r.get("description")
        return doc
