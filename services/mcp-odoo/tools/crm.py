# tools/crm.py
"""
DESARROLLO (Lectura y Escritura):
- dev_create_quotation: Crea un flujo completo: partner → lead → oportunidad → cotización
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel
import os


class QuotationResult(BaseModel):
    """Modelo para el resultado de crear una cotización."""

    partner_id: int
    partner_name: str
    lead_id: int
    lead_name: str
    opportunity_id: int
    opportunity_name: str
    sale_order_id: int
    sale_order_name: str
    environment: str = "development"
    steps: Dict[str, str]


class DevOdooCRMClient:
    """
    Cliente Odoo específico para el ambiente de DESARROLLO (CRM/Cotizaciones).
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

    def search_read(
        self, model: str, domain: list, fields: list, limit: int = 1
    ) -> list:
        """Busca y lee registros."""
        return self.execute_kw(
            model, "search_read", [domain], {"fields": fields, "limit": limit}
        )

    def create(self, model: str, values: Dict[str, Any]) -> int:
        """Crea un nuevo registro."""
        return self.execute_kw(model, "create", [values])

    def write(self, model: str, record_id: int, values: Dict[str, Any]) -> bool:
        """Actualiza un registro existente."""
        return self.execute_kw(model, "write", [[record_id], values])

    def read(self, model: str, record_id: int, fields: list = None) -> Dict[str, Any]:
        """Lee un registro por ID."""
        fields = fields or []
        result = self.execute_kw(model, "read", [[record_id]], {"fields": fields})
        return result[0] if result else {}

    def action_set_won(self, lead_id: int) -> bool:
        """Marca una oportunidad como ganada."""
        return self.execute_kw("crm.lead", "action_set_won", [[lead_id]])


def register(mcp, deps: dict):
    """
    Registra las herramientas MCP para CRM y Cotizaciones.

    DESARROLLO (Lectura y Escritura):
    - dev_create_quotation: Flujo completo para crear cotización desde lead
    """
    # Cliente de PRODUCCIÓN (solo lectura)
    odoo = deps["odoo"]

    # Cliente de DESARROLLO - lazy loading
    dev_client = None

    def get_dev_client():
        """Inicializa el cliente de desarrollo solo cuando se necesita."""
        nonlocal dev_client
        if dev_client is None:
            dev_client = DevOdooCRMClient()
        return dev_client

    @mcp.tool(
        name="dev_create_quotation",
        description="Crea una cotización completa en desarrollo: verifica/crea partner → crea lead → convierte a oportunidad → genera cotización",
    )
    def dev_create_quotation(
        partner_name: str,
        contact_name: str,
        email: str,
        phone: str,
        lead_name: str,
        user_id: Optional[int] = None,
        product_id: Optional[int] = None,
        product_qty: float = 1.0,
        product_price: Optional[float] = None,
    ) -> QuotationResult:
        """
        Crea una cotización completa siguiendo el flujo de ventas de Odoo.

        Flujo:
        1. Verifica si existe el partner (res.partner) por email, si no existe lo crea
        2. Crea un lead (crm.lead) tipo 'lead'
        3. Convierte el lead a oportunidad (type='opportunity')
        4. Genera una cotización/orden de venta asociada a la oportunidad

        Args:
            partner_name: Nombre del cliente/empresa
            contact_name: Nombre del contacto
            email: Email del contacto
            phone: Teléfono del contacto
            lead_name: Nombre del lead/oportunidad (ej: "Cotización Robot Limpieza")
            user_id: ID del vendedor (res.users), opcional
            product_id: ID del producto a cotizar, opcional
            product_qty: Cantidad del producto, default 1.0
            product_price: Precio unitario, opcional (usa precio del producto si no se especifica)

        Returns:
            QuotationResult con los IDs de todos los registros creados
        """
        client = get_dev_client()
        steps = {}

        # PASO 1: Verificar/Crear Partner (res.partner)
        # Buscar partner existente por email
        existing_partners = client.search_read(
            "res.partner",
            [("email", "=", email)],
            ["id", "name", "email"],
            limit=1,
        )

        if existing_partners:
            partner_id = existing_partners[0]["id"]
            partner_full_name = existing_partners[0]["name"]
            steps["partner"] = (
                f"Partner existente encontrado: {partner_full_name} (ID: {partner_id})"
            )
        else:
            # Crear nuevo partner
            partner_values = {
                "name": partner_name,
                "email": email,
                "phone": phone,
                "is_company": False,
                "type": "contact",
            }
            partner_id = client.create("res.partner", partner_values)
            partner_full_name = partner_name
            steps["partner"] = (
                f"Nuevo partner creado: {partner_full_name} (ID: {partner_id})"
            )

        # PASO 2: Crear Lead (crm.lead) tipo 'lead'
        lead_values = {
            "name": lead_name,
            "partner_name": partner_name,
            "contact_name": contact_name,
            "phone": phone,
            "email_from": email,
            "type": "lead",  # Tipo: lead
            "partner_id": partner_id,
        }

        if user_id:
            lead_values["user_id"] = user_id

        lead_id = client.create("crm.lead", lead_values)
        steps["lead"] = f"Lead creado: {lead_name} (ID: {lead_id})"

        # PASO 3: Convertir Lead a Oportunidad
        # Actualizar el lead a tipo 'opportunity' y establecer date_conversion
        from datetime import datetime

        conversion_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        client.write(
            "crm.lead",
            lead_id,
            {"type": "opportunity", "date_conversion": conversion_date},
        )
        steps["opportunity"] = (
            f"Lead convertido a oportunidad (ID: {lead_id}) - Fecha conversión: {conversion_date}"
        )

        # Leer el lead actualizado para obtener date_conversion
        lead_data = client.read(
            "crm.lead", lead_id, ["name", "date_conversion", "partner_id"]
        )

        # PASO 4: Generar Cotización (sale.order)
        # Crear orden de venta asociada a la oportunidad
        sale_values = {
            "partner_id": partner_id,
            "opportunity_id": lead_id,  # Asociar con la oportunidad
            "origin": lead_name,  # Referencia al origen
            "note": f"<p>Cotización generada desde oportunidad: {lead_name}</p>",
        }

        if user_id:
            sale_values["user_id"] = user_id

        sale_order_id = client.create("sale.order", sale_values)

        # Leer la orden creada para obtener el nombre
        sale_data = client.read("sale.order", sale_order_id, ["name"])
        sale_order_name = sale_data.get("name", f"S{sale_order_id}")

        steps["sale_order"] = (
            f"Cotización creada: {sale_order_name} (ID: {sale_order_id})"
        )

        # PASO 5 (Opcional): Agregar línea de producto si se especificó
        if product_id:
            line_values = {
                "order_id": sale_order_id,
                "product_id": product_id,
                "product_uom_qty": product_qty,
            }

            if product_price:
                line_values["price_unit"] = product_price

            line_id = client.create("sale.order.line", line_values)
            steps["product_line"] = f"Línea de producto agregada (ID: {line_id})"

        # Verificar que la orden esté asociada a la oportunidad
        opportunity_data = client.read("crm.lead", lead_id, ["order_ids"])

        return QuotationResult(
            partner_id=partner_id,
            partner_name=partner_full_name,
            lead_id=lead_id,
            lead_name=lead_name,
            opportunity_id=lead_id,  # El ID es el mismo (lead → opportunity)
            opportunity_name=lead_data.get("name", lead_name),
            sale_order_id=sale_order_id,
            sale_order_name=sale_order_name,
            steps=steps,
        )
