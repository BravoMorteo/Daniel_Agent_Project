import os
import xmlrpc.client

class OdooClient:
    """Cliente base (solo conexión y utilidades genéricas)."""
    def __init__(self, url: str | None = None, db: str | None = None,
                 username: str | None = None, password: str | None = None):
        self.url = (url or os.environ["ODOO_URL"]).rstrip("/")
        self.db = db or os.environ["ODOO_DB"]
        self.username = username or os.environ["ODOO_LOGIN"]
        # Usa API key como password
        self.password = password or os.environ["ODOO_API_KEY"]

        self.common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")
        self.uid = self.common.authenticate(self.db, self.username, self.password, {})

    def execute_kw(self, model: str, method: str, args=None, kwargs=None):
        args = args or []
        kwargs = kwargs or {}
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model, method, args, kwargs
        )

    def search_read(self, model: str, domain=None, fields=None, limit: int = 50):
        domain = domain or []
        fields = fields or ["id", "name"]
        return self.execute_kw(model, "search_read", [domain], {"fields": fields, "limit": limit})
