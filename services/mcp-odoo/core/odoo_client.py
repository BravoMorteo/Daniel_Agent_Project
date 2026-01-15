import os
import xmlrpc.client


class OdooClient:
    """Cliente base (solo conexión y utilidades genéricas)."""

    def __init__(
        self,
        url: str | None = None,
        db: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ):
        self.url = (url or os.environ["ODOO_URL"]).rstrip("/")
        self.db = db or os.environ["ODOO_DB"]
        self.username = username or os.environ["ODOO_LOGIN"]
        # Usa API key como password
        self.password = password or os.environ["ODOO_API_KEY"]

        # Conexión XML-RPC con allow_none=True para manejar valores None de Odoo
        self.common = xmlrpc.client.ServerProxy(
            f"{self.url}/xmlrpc/2/common", allow_none=True
        )
        self.models = xmlrpc.client.ServerProxy(
            f"{self.url}/xmlrpc/2/object", allow_none=True
        )
        self.uid = self.common.authenticate(self.db, self.username, self.password, {})

    def execute_kw(self, model: str, method: str, args=None, kwargs=None):
        args = args or []
        kwargs = kwargs or {}
        return self.models.execute_kw(
            self.db, self.uid, self.password, model, method, args, kwargs
        )

    def search_read(self, model: str, domain=None, fields=None, limit: int = 50):
        domain = domain or []
        fields = fields or ["id", "name"]
        return self.execute_kw(
            model, "search_read", [domain], {"fields": fields, "limit": limit}
        )

    def create(self, model: str, values: dict) -> int:
        """Crea un registro en Odoo."""
        return self.execute_kw(model, "create", [values])

    def write(self, model: str, record_id: int, values: dict) -> bool:
        """Actualiza un registro en Odoo."""
        return self.execute_kw(model, "write", [[record_id], values])

    def read(self, model: str, record_id: int, fields: list = None):
        """Lee un registro específico de Odoo."""
        fields = fields or []
        result = self.execute_kw(model, "read", [[record_id]], {"fields": fields})
        return result[0] if result else None

    def get_salesperson_with_least_opportunities(self) -> int | None:
        """
        Obtiene el ID del vendedor (user) con menos oportunidades activas.

        Criterios:
        - Obtiene miembros del equipo de ventas servibot (ID 14)
        - Solo cuenta oportunidades activas (type='opportunity')
        - Solo cuenta oportunidades en etapas específicas (1, 2, 10, 3)
        - Retorna el user_id con menor cantidad de oportunidades activas

        Returns:
            int: ID del vendedor con menos carga, o None si no hay vendedores
        """
        # 1. Obtener miembros del equipo de ventas servibot (ID 14)
        teams = self.search_read(
            "crm.team",
            [("id", "in", [14])],
            ["member_ids"],
        )

        members_ids = set()
        for team in teams:
            members_ids.update(team.get("member_ids", []))

        members_ids = list(members_ids)

        if not members_ids:
            return None

        # 2. Inicializar contador para TODOS los miembros del equipo
        users_info = self.search_read(
            "res.users",
            [("id", "in", members_ids)],
            ["id", "name"],
            limit=len(members_ids),
        )

        # Ordenar por ID para orden determinístico
        users_info_sorted = sorted(users_info, key=lambda u: u["id"])

        opportunities_by_user = {}
        for user in users_info_sorted:
            opportunities_by_user[user["id"]] = {
                "name": user["name"],
                "count": 0,
            }

        # 3. Obtener todas las oportunidades activas en etapas específicas
        leads = self.search_read(
            "crm.lead",
            [
                ("stage_id", "in", [1, 2, 10, 3]),
                ("active", "=", True),
                ("type", "=", "opportunity"),
            ],
            ["user_id"],
            limit=1000,  # Límite alto para obtener todas las oportunidades
        )

        # 4. Contar oportunidades activas por vendedor
        for lead in leads:
            user_info = lead.get("user_id")

            # Filtrar solo usuarios que están en los equipos
            if not user_info or user_info[0] not in members_ids:
                continue

            user_id = user_info[0]

            # Asegurarse de que el usuario esté en el diccionario
            if user_id in opportunities_by_user:
                opportunities_by_user[user_id]["count"] += 1

        # 5. Si no hay oportunidades asignadas, retornar el primer vendedor
        if not opportunities_by_user:
            return None

        # 6. Encontrar el vendedor con menos oportunidades
        least_user_id = min(
            opportunities_by_user, key=lambda uid: opportunities_by_user[uid]["count"]
        )

        return least_user_id
