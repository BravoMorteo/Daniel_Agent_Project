"""
Search Tools
============
Tools de búsqueda y recuperación de documentos (proyectos y tareas).
"""

from typing import Dict, Any, List
from core import encode_content, odoo_form_url, wants_projects, wants_tasks


def register_search_tools(mcp, deps):
    """Registra los tools de búsqueda en MCP"""

    @mcp.tool(
        name="search",
        description="Busca en Odoo proyectos y/o tareas según el query. Devuelve results[] con id/title/url.",
    )
    def mcp_search(query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Busca proyectos y/o tareas en Odoo.

        Args:
            query: cadena de búsqueda (ilike)
            limit: máximo de resultados total

        Returns (content array, type=text, JSON string):
          {"results":[{"id":"project:1","title":"Project · X","url":"..."},
                      {"id":"task:2","title":"Task · Y","url":"..."}]}
        """
        odoo = deps["odoo"]
        want_p = wants_projects(query)
        want_t = wants_tasks(query)

        if not (want_p or want_t):
            # Si no detecta, buscamos en ambos
            want_p = want_t = True

        # Dividimos el límite (p. ej. mitad y mitad) si se buscan ambos
        lim_p = limit if want_p and not want_t else max(1, limit // 2) if want_p else 0
        lim_t = limit if want_t and not want_p else max(1, limit // 2) if want_t else 0

        results: List[Dict[str, Any]] = []

        # Buscar proyectos
        if want_p and lim_p:
            domain = [["name", "ilike", query]] if query else []
            rows = odoo.search_read(
                "project.project", domain, ["id", "name", "active"], lim_p
            )
            for r in rows:
                pid = int(r["id"])
                results.append(
                    {
                        "id": f"project:{pid}",
                        "title": f"Project · {r.get('name','(sin nombre)')}",
                        "url": odoo_form_url("project.project", pid),
                    }
                )

        # Buscar tareas
        if want_t and lim_t:
            domain = [["name", "ilike", query]] if query else []
            rows = odoo.search_read(
                "project.task",
                domain,
                ["id", "name", "project_id", "user_id", "stage_id", "date_deadline"],
                lim_t,
            )
            for r in rows:
                tid = int(r["id"])
                results.append(
                    {
                        "id": f"task:{tid}",
                        "title": f"Task · {r.get('name','(sin nombre)')}",
                        "url": odoo_form_url("project.task", tid),
                    }
                )

        return encode_content({"results": results})

    @mcp.tool(
        name="fetch",
        description="Recupera el documento completo por id (project:<id> o task:<id>) con texto y metadatos.",
    )
    def mcp_fetch(doc_id: str) -> Dict[str, Any]:
        """
        Recupera detalles completos de un proyecto o tarea.

        Args:
            doc_id: "project:<id>" o "task:<id>"

        Returns (content array, type=text, JSON string):
          {"id":"task:123","title":"...","text":"...","url":"...","metadata":{...}}
        """
        odoo = deps["odoo"]

        if ":" not in doc_id:
            return encode_content(
                {"error": "Invalid id format. Use 'project:<id>' or 'task:<id>'."}
            )

        kind, raw_id = doc_id.split(":", 1)
        try:
            rid = int(raw_id)
        except ValueError:
            return encode_content({"error": "Invalid numeric id."})

        # Fetch proyecto
        if kind == "project":
            rows = odoo.search_read(
                "project.project", [["id", "=", rid]], ["id", "name", "active"], 1
            )
            if not rows:
                return encode_content({"error": f"Project {rid} not found"})

            r = rows[0]
            title = f"Project · {r.get('name','(sin nombre)')}"
            text = r.get("name", "")
            url = odoo_form_url("project.project", rid)

            doc = {
                "id": f"project:{rid}",
                "title": title,
                "text": text,
                "url": url,
                "metadata": {
                    "model": "project.project",
                    "active": r.get("active", True),
                },
            }
            return encode_content(doc)

        # Fetch tarea
        if kind == "task":
            rows = odoo.search_read(
                "project.task",
                [["id", "=", rid]],
                [
                    "id",
                    "name",
                    "project_id",
                    "user_id",
                    "stage_id",
                    "date_deadline",
                    "description",
                ],
                1,
            )
            if not rows:
                return encode_content({"error": f"Task {rid} not found"})

            r = rows[0]
            title = f"Task · {r.get('name','(sin nombre)')}"
            text = (r.get("description") or r.get("name") or "").strip()
            url = odoo_form_url("project.task", rid)

            # project_id/user_id/stage_id suelen venir como [id, "Nombre"]
            meta: Dict[str, Any] = {"model": "project.task"}
            for key in ("project_id", "user_id", "stage_id"):
                val = r.get(key)
                if isinstance(val, list) and len(val) >= 1:
                    meta[key] = {"id": val[0], "name": val[1] if len(val) > 1 else None}
                else:
                    meta[key] = val
            meta["date_deadline"] = r.get("date_deadline")

            doc = {
                "id": f"task:{rid}",
                "title": title,
                "text": text,
                "url": url,
                "metadata": meta,
            }
            return encode_content(doc)

        return encode_content(
            {"error": f"Unknown kind '{kind}'. Use 'project' or 'task'."}
        )
