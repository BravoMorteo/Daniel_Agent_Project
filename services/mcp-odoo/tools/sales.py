# tools/sales.py
"""
PRODUCCIÓN (Solo Lectura):
- list_sales: lista órdenes de venta con filtros
- get_sale: obtiene detalles de una orden específica

DESARROLLO (Lectura y Escritura):
- dev_create_sale: crea orden de venta en desarrollo
- dev_create_sale_line: agrega línea a orden en desarrollo
- dev_update_sale: actualiza orden existente en desarrollo
- dev_read_sale: lee orden desde desarrollo
"""
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, field_validator
import os


class SaleOrder(BaseModel):
    """Modelo para órdenes de venta (sale.order)."""

    id: int
    name: str
    partner_id: Any
    date_order: Optional[str] = None
    amount_total: float = 0.0
    state: Optional[str] = None
    user_id: Any = None

    @field_validator("date_order", mode="before")
    def _normalize_date(cls, v):
        if v is False or v is None or v == "":
            return None
        return str(v)


class DevSaleOrder(BaseModel):
    """Modelo para órdenes creadas en desarrollo."""

    id: int
    model: str = "sale.order"
    values: Dict[str, Any]
    environment: str = "development"


class DevOdooSalesClient:
    """
    Cliente Odoo específico para el ambiente de DESARROLLO (ventas).
    Se conecta a: pegasuscontrol-dev18-25468489.dev.odoo.com
    """

    def __init__(self):
        import xmlrpc.client

        # Configuración específica para DESARROLLO
        self.url = os.environ.get(
            "DEV_ODOO_URL", "https://pegasuscontrol-dev18-25468489.dev.odoo.com"
        ).rstrip("/")
        self.db = os.environ.get("DEV_ODOO_DB", "pegasuscontrol-dev18-25468489")
        self.username = os.environ.get("DEV_ODOO_LOGIN")
        self.password = os.environ.get("DEV_ODOO_API_KEY")

        if not self.username or not self.password:
            raise ValueError(
                "Faltan credenciales DEV_ODOO_LOGIN o DEV_ODOO_API_KEY en .env"
            )

        # Conexión XML-RPC a desarrollo
        self.common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")

        # Autenticación
        self.uid = self.common.authenticate(self.db, self.username, self.password, {})

        if not self.uid:
            raise ValueError("No se pudo autenticar en el ambiente de desarrollo")

    def execute_kw(self, model: str, method: str, args=None, kwargs=None):
        """Ejecuta un método en el modelo especificado."""
        args = args or []
        kwargs = kwargs or {}
        return self.models.execute_kw(
            self.db, self.uid, self.password, model, method, args, kwargs
        )

    def create(self, model: str, values: Dict[str, Any]) -> int:
        """Crea un nuevo registro en el modelo especificado."""
        return self.execute_kw(model, "create", [values])

    def write(self, model: str, record_id: int, values: Dict[str, Any]) -> bool:
        """Actualiza un registro existente."""
        return self.execute_kw(model, "write", [[record_id], values])

    def read(
        self, model: str, record_id: int, fields: List[str] = None
    ) -> Dict[str, Any]:
        """Lee un registro por su ID."""
        fields = fields or []
        result = self.execute_kw(model, "read", [[record_id]], {"fields": fields})
        return result[0] if result else {}


def register(mcp, deps: dict):
    """
    Registra las herramientas MCP para Órdenes de Venta.

    PRODUCCIÓN (Solo Lectura):
    - list_sales, get_sale

    DESARROLLO (Lectura y Escritura):
    - dev_create_sale, dev_create_sale_line, dev_update_sale, dev_read_sale
    """
    # Cliente de PRODUCCIÓN (solo lectura)
    odoo = deps["odoo"]

    # Cliente de DESARROLLO (lectura y escritura) - lazy loading
    dev_client = None

    def get_dev_client():
        """Inicializa el cliente de desarrollo solo cuando se necesita."""
        nonlocal dev_client
        if dev_client is None:
            dev_client = DevOdooSalesClient()
        return dev_client

    @mcp.tool(
        name="list_sales",
        description="Listar órdenes de venta (sale.order) con filtros opcionales",
    )
    def list_sales(
        partner_id: Optional[int] = None,
        user_id: Optional[int] = None,
        state: Optional[str] = None,
        q: Optional[str] = None,
        limit: int = 50,
    ) -> List[SaleOrder]:
        """
        Lista órdenes de venta desde Odoo.

        Args:
            partner_id: Filtrar por cliente (res.partner id).
            user_id: Filtrar por vendedor (res.users id).
            state: Filtrar por estado ('draft', 'sent', 'sale', 'done', 'cancel').
            q: Búsqueda por nombre/referencia de la orden (ilike).
            limit: Límite de resultados (por defecto 50).

        Returns:
            Lista de SaleOrder (id, name, partner_id, date_order, amount_total, state, user_id).
        """
        domain = []

        if partner_id:
            domain.append(["partner_id", "=", int(partner_id)])

        if user_id:
            domain.append(["user_id", "=", int(user_id)])

        if state:
            domain.append(["state", "=", state])

        if q:
            domain.append(["name", "ilike", q])

        fields = [
            "id",
            "name",
            "partner_id",
            "date_order",
            "amount_total",
            "state",
            "user_id",
        ]
        rows = odoo.search_read("sale.order", domain, fields, limit)

        sales: List[SaleOrder] = []
        for r in rows:
            payload = {
                "id": r["id"],
                "name": r.get("name") or "",
                "partner_id": r.get("partner_id"),
                "date_order": r.get("date_order"),
                "amount_total": r.get("amount_total", 0.0),
                "state": r.get("state"),
                "user_id": r.get("user_id"),
            }
            sales.append(SaleOrder.model_validate(payload))
        return sales

    @mcp.tool(
        name="get_sale",
        description="Obtener detalle completo de una orden de venta por id",
    )
    def get_sale(sale_id: int, include_lines: bool = False) -> Dict[str, Any]:
        """
        Obtiene los detalles de una orden de venta específica.

        Args:
            sale_id: ID de la orden de venta.
            include_lines: Si True, incluye las líneas de la orden (order_line).

        Returns:
            Diccionario con los datos de la orden de venta.
        """
        fields = [
            "id",
            "name",
            "partner_id",
            "date_order",
            "amount_total",
            "amount_untaxed",
            "amount_tax",
            "state",
            "user_id",
            "payment_term_id",
            "validity_date",
            "note",
        ]

        if include_lines:
            fields.append("order_line")

        rows = odoo.search_read("sale.order", [["id", "=", int(sale_id)]], fields, 1)

        if not rows:
            return {"error": f"Sale order {sale_id} not found"}

        r = rows[0]

        # Construir el documento de respuesta
        doc = SaleOrder.model_validate(
            {
                "id": r["id"],
                "name": r.get("name") or "",
                "partner_id": r.get("partner_id"),
                "date_order": r.get("date_order"),
                "amount_total": r.get("amount_total", 0.0),
                "state": r.get("state"),
                "user_id": r.get("user_id"),
            }
        ).model_dump()

        # Agregar campos adicionales
        doc["amount_untaxed"] = r.get("amount_untaxed", 0.0)
        doc["amount_tax"] = r.get("amount_tax", 0.0)
        doc["payment_term_id"] = r.get("payment_term_id")
        doc["validity_date"] = r.get("validity_date")
        doc["note"] = r.get("note")

        # Si se solicitan las líneas de la orden
        if include_lines and r.get("order_line"):
            line_ids = r["order_line"]
            if isinstance(line_ids, list) and line_ids:
                # Leer las líneas de la orden
                lines = odoo.search_read(
                    "sale.order.line",
                    [["id", "in", line_ids]],
                    [
                        "id",
                        "product_id",
                        "name",
                        "product_uom_qty",
                        "price_unit",
                        "price_subtotal",
                    ],
                    len(line_ids),
                )
                doc["order_lines"] = lines
            else:
                doc["order_lines"] = []

        return doc

    # ═══════════════════════════════════════════════════════════════
    # HERRAMIENTAS DE DESARROLLO (Escritura en ambiente de desarrollo)
    # ═══════════════════════════════════════════════════════════════

    @mcp.tool(
        name="dev_create_sale",
        description="Crea una orden de venta en el ambiente de DESARROLLO (no producción)",
    )
    def dev_create_sale(
        partner_id: int,
        user_id: Optional[int] = None,
        date_order: Optional[str] = None,
        payment_term_id: Optional[int] = None,
        note: Optional[str] = None,
    ) -> DevSaleOrder:
        """
        Crea una nueva orden de venta en la base de datos de DESARROLLO.

        Args:
            partner_id: ID del cliente (res.partner) - REQUERIDO
            user_id: ID del vendedor (res.users) - opcional
            date_order: Fecha de la orden (formato: YYYY-MM-DD HH:MM:SS) - opcional
            payment_term_id: ID de los términos de pago - opcional
            note: Notas u observaciones - opcional

        Returns:
            DevSaleOrder con los datos de la orden creada

        Ejemplo:
            dev_create_sale(
                partner_id=23,
                user_id=5,
                note="Orden de prueba - Cliente preferente"
            )
        """
        client = get_dev_client()

        # Valores para crear la orden
        values = {
            "partner_id": partner_id,
        }

        if user_id:
            values["user_id"] = user_id
        if date_order:
            values["date_order"] = date_order
        if payment_term_id:
            values["payment_term_id"] = payment_term_id
        if note:
            values["note"] = note

        # Crear el registro
        sale_id = client.create("sale.order", values)

        return DevSaleOrder(id=sale_id, model="sale.order", values=values)

    @mcp.tool(
        name="dev_create_sale_line",
        description="Agrega una línea de producto a una orden de venta en DESARROLLO",
    )
    def dev_create_sale_line(
        order_id: int,
        product_id: int,
        product_uom_qty: float = 1.0,
        price_unit: Optional[float] = None,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Agrega una línea de producto a una orden de venta en DESARROLLO.

        Args:
            order_id: ID de la orden de venta - REQUERIDO
            product_id: ID del producto - REQUERIDO
            product_uom_qty: Cantidad (default: 1.0)
            price_unit: Precio unitario (opcional, se calcula automáticamente si no se especifica)
            name: Descripción del producto (opcional)

        Returns:
            Diccionario con el resultado de la creación

        Ejemplo:
            dev_create_sale_line(
                order_id=145,
                product_id=12,
                product_uom_qty=10.0,
                price_unit=500.00
            )
        """
        client = get_dev_client()

        # Valores para crear la línea
        values = {
            "order_id": order_id,
            "product_id": product_id,
            "product_uom_qty": product_uom_qty,
        }

        if price_unit is not None:
            values["price_unit"] = price_unit
        if name:
            values["name"] = name

        # Crear la línea
        line_id = client.create("sale.order.line", values)

        return {
            "success": True,
            "line_id": line_id,
            "order_id": order_id,
            "values": values,
            "environment": "development",
        }

    @mcp.tool(
        name="dev_update_sale",
        description="Actualiza una orden de venta existente en el ambiente de DESARROLLO",
    )
    def dev_update_sale(sale_id: int, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza una orden de venta existente en DESARROLLO.

        Args:
            sale_id: ID de la orden a actualizar - REQUERIDO
            values: Diccionario con los campos a actualizar

        Returns:
            Diccionario con el resultado de la actualización

        Ejemplo:
            dev_update_sale(
                sale_id=145,
                values={
                    "note": "Orden actualizada - Envío urgente",
                    "payment_term_id": 2
                }
            )
        """
        client = get_dev_client()

        # Actualizar el registro
        success = client.write("sale.order", sale_id, values)

        return {
            "success": success,
            "model": "sale.order",
            "sale_id": sale_id,
            "updated_values": values,
            "environment": "development",
        }

    @mcp.tool(
        name="dev_read_sale",
        description="Lee una orden de venta del ambiente de DESARROLLO para verificar datos",
    )
    def dev_read_sale(
        sale_id: int, fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Lee una orden de venta del ambiente de DESARROLLO.

        Args:
            sale_id: ID de la orden a leer - REQUERIDO
            fields: Lista de campos a leer (None = todos los campos)

        Returns:
            Diccionario con los datos de la orden

        Ejemplo:
            dev_read_sale(
                sale_id=145,
                fields=["name", "partner_id", "amount_total", "state"]
            )
        """
        client = get_dev_client()

        # Leer el registro
        record = client.read("sale.order", sale_id, fields or [])

        return {"record": record, "model": "sale.order", "environment": "development"}
