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

        # Conexión XML-RPC a desarrollo con allow_none=True para manejar valores None
        self.common = xmlrpc.client.ServerProxy(
            f"{self.url}/xmlrpc/2/common", allow_none=True
        )
        self.models = xmlrpc.client.ServerProxy(
            f"{self.url}/xmlrpc/2/object", allow_none=True
        )

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

    def get_salesperson_with_least_opportunities(self) -> int | None:
        """
        Obtiene el ID del vendedor (user) con menos oportunidades activas.

        Criterios:
        - Obtiene miembros de los equipos de ventas (ID 1 y 14)
        - Solo cuenta oportunidades activas (type='opportunity')
        - Solo cuenta oportunidades en etapas específicas (1, 2, 10, 3)
        - Retorna el user_id con menor cantidad de oportunidades activas

        Returns:
            int: ID del vendedor con menos carga, o None si no hay vendedores
        """
        # 1. Obtener miembros de los equipos de ventas (ID 1 y 14)
        teams = self.search_read(
            "crm.team",
            [("id", "in", [14])],  # 14 es el equipo de ventas servibot
            ["member_ids"],
        )

        members_ids = set()
        for team in teams:
            members_ids.update(team.get("member_ids", []))

        members_ids = list(members_ids)

        if not members_ids:
            return None

        # 2. Inicializar contador para TODOS los miembros del equipo
        # Primero obtenemos los nombres de todos los miembros
        users_info = self.search_read(
            "res.users",
            [("id", "in", members_ids)],
            ["id", "name"],
            limit=len(members_ids),  # Asegurar que obtenemos TODOS los miembros
        )

        # Ordenar por ID para orden determinístico
        users_info_sorted = sorted(users_info, key=lambda u: u["id"])

        opportunities_by_user = {}
        for user in users_info_sorted:
            opportunities_by_user[user["id"]] = {
                "name": user["name"],
                "count": 0,
            }  # 3. Obtener todas las oportunidades activas en etapas específicas
        leads = self.search_read(
            "crm.lead",
            [
                ("stage_id", "in", [1, 2, 10, 3]),
                ("active", "=", True),
                ("type", "=", "opportunity"),
            ],
            ["user_id"],
            limit=None,  # Sin límite para obtener todas
        )

        # 4. Contar oportunidades activas por vendedor
        for lead in leads:
            user_info = lead.get("user_id")

            # Filtrar solo usuarios que están en los equipos
            if not user_info or user_info[0] not in members_ids:
                continue

            user_id = user_info[0]

            # Incrementar el contador (ya está inicializado)
            if user_id in opportunities_by_user:
                opportunities_by_user[user_id]["count"] += 1

        # 5. Encontrar el vendedor con menos oportunidades
        if not opportunities_by_user:
            return None

        # Usar el count como criterio principal y el user_id como desempate (menor ID gana)
        least_user_id = min(
            opportunities_by_user,
            key=lambda uid: (opportunities_by_user[uid]["count"], uid),
        )

        return least_user_id


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
        description="Crea una cotización completa en desarrollo: verifica/crea partner → asigna vendedor por balanceo de carga → crea lead → convierte a oportunidad → genera cotización",
    )
    def dev_create_quotation(
        partner_name: str,
        contact_name: str,
        email: str,
        phone: str,
        lead_name: str,
        user_id: int = 0,
        product_id: int = 0,
        product_qty: float = 1.0,
        product_price: float = -1.0,
    ) -> QuotationResult:
        """
        Crea una cotización completa siguiendo el flujo de ventas de Odoo.

        Flujo:
        1. Verifica si existe el partner (res.partner) por email, si no existe lo crea
           - Búsqueda EXACTA por campo 'email' en res.partner
           - Si existe: reutiliza el partner
           - Si NO existe: crea nuevo partner con los datos proporcionados
        1.5. Asigna vendedor (user_id) automáticamente si no se especifica
           - Aplica balanceo de carga: asigna al vendedor con menos oportunidades activas
           - Excluye oportunidades ganadas y perdidas del conteo
        2. Crea un lead (crm.lead) tipo 'lead' con email_from
        3. Convierte el lead a oportunidad (type='opportunity')
        4. Genera una cotización/orden de venta asociada a la oportunidad

        Args:
            partner_name: Nombre del cliente/empresa
            contact_name: Nombre del contacto
            email: Email del contacto (se busca en res.partner.email y se guarda en crm.lead.email_from)
            phone: Teléfono del contacto
            lead_name: Nombre del lead/oportunidad (ej: "Cotización Robot Limpieza")
            user_id: ID del vendedor (res.users), 0 = asignación automática por balanceo de carga
            product_id: ID del producto a cotizar, 0 = sin producto
            product_qty: Cantidad del producto, default 1.0
            product_price: Precio unitario manual, -1.0 = obtiene automáticamente el precio del producto

        Returns:
            QuotationResult con los IDs de todos los registros creados

        Nota:
            - La búsqueda de partners es por email EXACTO (no parcial)
            - El email se guarda como 'email' en res.partner y como 'email_from' en crm.lead
        """
        client = get_dev_client()
        steps = {}

        # PASO 1: Verificar/Crear Partner (res.partner)
        # Buscar partner existente por email (el campo en res.partner es 'email')
        # pero usamos el valor que viene en el parámetro 'email' que se guardará como 'email_from' en el lead
        email_normalizado = email.strip().lower()
        existing_partners = client.search_read(
            "res.partner",
            [("email", "=", email_normalizado)],  # Busca en res.partner.email
            ["id", "name", "email", "phone"],
            limit=1,
        )

        if existing_partners:
            partner_id = existing_partners[0]["id"]
            partner_full_name = existing_partners[0]["name"]
            steps["partner"] = (
                f"✓ Partner existente encontrado por email '{email}': {partner_full_name} (ID: {partner_id})"
            )
        else:
            # Crear nuevo partner
            partner_values = {
                "name": contact_name,
                "email": email_normalizado,  # Se guarda en res.partner.email
                "phone": phone,
                "is_company": False,
                "type": "contact",
            }
            partner_id = client.create("res.partner", partner_values)
            partner_full_name = partner_name
            steps["partner"] = (
                f"✓ Nuevo partner creado con email '{email}': {partner_full_name} (ID: {partner_id})"
            )

        # PASO 1.5: Asignar vendedor si no se especificó
        assigned_user_id = user_id
        if not assigned_user_id:
            # Aplicar balanceo de carga: asignar al vendedor con menos oportunidades activas
            assigned_user_id = client.get_salesperson_with_least_opportunities()
            if assigned_user_id:
                steps["user_assignment"] = (
                    f"✓ Vendedor asignado automáticamente por balanceo de carga (ID: {assigned_user_id})"
                )
            else:
                steps["user_assignment"] = (
                    "⚠️ No se pudo asignar vendedor automáticamente (no hay usuarios disponibles)"
                )
        else:
            steps["user_assignment"] = (
                f"✓ Vendedor especificado manualmente (ID: {assigned_user_id})"
            )

        # PASO 2: Crear Lead (crm.lead) tipo 'lead'
        lead_values = {
            "name": lead_name,
            "partner_name": partner_name,
            "contact_name": contact_name,
            "phone": phone,
            "email_from": email_normalizado,
            "type": "lead",  # Tipo: lead
            "partner_id": partner_id,
        }

        if assigned_user_id:
            lead_values["user_id"] = assigned_user_id

        lead_id = client.create("crm.lead", lead_values)
        steps["lead"] = f"Lead creado: {lead_name} (ID: {lead_id})"

        # PASO 3: Convertir Lead a Oportunidad
        # Actualizar el lead a tipo 'opportunity' y establecer date_conversion
        from datetime import datetime

        conversion_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Preparar valores de actualización
        opportunity_values = {
            "type": "opportunity",
            "date_conversion": conversion_date,
            "stage_id": 3,  # 3 = Oportunidad en etapa cotizacion
        }

        # Asegurar que el user_id se mantenga en la oportunidad
        if assigned_user_id:
            opportunity_values["user_id"] = assigned_user_id

        client.write("crm.lead", lead_id, opportunity_values)
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

        if assigned_user_id:
            sale_values["user_id"] = assigned_user_id

        sale_order_id = client.create("sale.order", sale_values)

        # Leer la orden creada para obtener el nombre
        sale_data = client.read("sale.order", sale_order_id, ["name"])
        sale_order_name = sale_data.get("name", f"S{sale_order_id}")

        steps["sale_order"] = (
            f"Cotización creada: {sale_order_name} (ID: {sale_order_id})"
        )

        # PASO 5 (Opcional): Agregar línea de producto si se especificó
        if product_id > 0:
            line_values = {
                "order_id": sale_order_id,
                "product_id": product_id,
                "product_uom_qty": product_qty,
            }

            # Si se especifica precio manual (> 0), usarlo
            if product_price > 0:
                line_values["price_unit"] = product_price
                steps["product_line_note"] = (
                    f"Precio manual especificado: ${product_price}"
                )
            else:
                # Buscar el precio en la pricelist ID 82 (Clientes Nacionales)
                pricelist_id = 82
                product_data = client.read("product.product", product_id, ["name"])
                product_name = product_data.get("name", "Unknown")

                # Buscar el item en la pricelist para este producto
                pricelist_items = client.search_read(
                    "product.pricelist.item",
                    [
                        ["pricelist_id", "=", pricelist_id],
                        ["product_id", "=", product_id],
                    ],
                    ["fixed_price", "compute_price"],
                )

                if pricelist_items and len(pricelist_items) > 0:
                    # Usar el precio del pricelist
                    pricelist_price = pricelist_items[0].get("fixed_price", 0.0)
                    line_values["price_unit"] = pricelist_price
                    steps["product_line_note"] = (
                        f"Precio obtenido del Pricelist (ID: {pricelist_id}) para '{product_name}': ${pricelist_price}"
                    )
                else:
                    # Si no está en el pricelist, usar list_price como fallback
                    product_data_full = client.read(
                        "product.product", product_id, ["list_price"]
                    )
                    auto_price = product_data_full.get("list_price", 0.0)
                    line_values["price_unit"] = auto_price
                    steps["product_line_note"] = (
                        f"Precio obtenido del producto '{product_name}' (no encontrado en pricelist): ${auto_price}"
                    )

            line_id = client.create("sale.order.line", line_values)
            steps["product_line"] = f"Línea de producto agregada (ID: {line_id})"

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
