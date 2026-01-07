# tools/crm.py
"""
DESARROLLO (Lectura y Escritura):
- dev_create_quotation: Crea un flujo completo: partner → lead → oportunidad → cotización
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import os
from datetime import datetime
from core.tasks import TaskStatus


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
        description="Crea una cotización completa de forma ASÍNCRONA con tracking y logging S3. Retorna tracking_id para consultar estado después. Para obtener el resultado completo, usar dev_get_quotation_status con el tracking_id retornado.",
    )
    def dev_create_quotation(
        partner_name: str,
        contact_name: str,
        email: str,
        phone: str,
        lead_name: str,
        ciudad: Optional[str] = None,
        user_id: int = 0,
        product_id: int = 0,
        product_qty: float = 1.0,
        product_price: float = -1.0,
        products: Optional[List[dict]] = None,
        description: Optional[str] = None,
        x_studio_producto: Optional[int] = None,
    ) -> dict:
        """
        Crea una cotización de forma ASÍNCRONA usando la infraestructura de FastAPI.

        NUEVO COMPORTAMIENTO:
        - Crea tarea en TaskManager
        - Ejecuta proceso en background
        - Registra logs en JSON + S3
        - Retorna tracking_id inmediatamente
        - LLM puede consultar estado con dev_get_quotation_status()
        - Soporta múltiples productos mediante el parámetro 'products'

        Flujo completo (ejecutado en background):
        1. Verifica si existe el partner (res.partner) por email, si no existe lo crea
        2. Asigna vendedor automáticamente si no se especifica (balanceo de carga)
        3. Crea un lead (crm.lead) tipo 'lead' con campos personalizados
        4. Convierte el lead a oportunidad
        5. Genera cotización/orden de venta
        6. Agrega líneas de productos (soporta múltiples productos)

        Args:
            partner_name: Nombre del cliente/empresa
            contact_name: Nombre del contacto
            email: Email del contacto
            phone: Teléfono del contacto
            lead_name: Nombre del lead/oportunidad
            ciudad: Ciudad del contacto (opcional)
            user_id: ID del vendedor (0 = asignación automática)
            product_id: ID del producto (0 = sin producto) [LEGACY - usar 'products']
            product_qty: Cantidad del producto [LEGACY - usar 'products']
            product_price: Precio manual (-1.0 = automático) [LEGACY - usar 'products']
            products: Lista de productos con formato [{"product_id": int, "qty": float, "price": float}]
            description: Descripción personalizada para el lead
            x_studio_producto: ID del producto principal (Many2one). Si se omite, se asigna automáticamente el primer producto

        Returns:
            dict con tracking_id, status, message, estimated_time

        Ejemplo retorno:
            {
                "tracking_id": "quot_abc123",
                "status": "queued",
                "message": "Cotización creada en cola de procesamiento",
                "estimated_time": "20-30 segundos",
                "info": "Usa dev_get_quotation_status(tracking_id) para consultar estado"
            }

        Ejemplo con múltiples productos:
            dev_create_quotation(
                partner_name="ACME Corp",
                contact_name="John Doe",
                email="john@acme.com",
                phone="+1234567890",
                lead_name="Restaurant Equipment Quote",
                products=[
                    {"product_id": 26156, "qty": 10, "price": 9350.0},
                    {"product_id": 26153, "qty": 20, "price": 8500.0}
                ],
                description="Equipment for new restaurant location"
            )
        """
        import uuid
        import threading

        # Importar TaskManager y Logger
        from core.tasks import task_manager
        from core.logger import quotation_logger

        # Generar tracking_id único
        tracking_id = f"quot_{uuid.uuid4().hex[:12]}"

        # Preparar parámetros
        params = {
            "partner_name": partner_name,
            "contact_name": contact_name,
            "email": email,
            "phone": phone,
            "lead_name": lead_name,
            "user_id": user_id,
            "product_id": product_id,
            "product_qty": product_qty,
            "product_price": product_price,
            "products": products,
            "description": description,
            "x_studio_producto": x_studio_producto,
        }

        # Crear tarea en TaskManager
        task_manager.create_task(tracking_id, params)

        # Log inicial
        quotation_logger.log_quotation(
            tracking_id=tracking_id, input_data=params, status="started"
        )

        # Lanzar proceso en background (thread separado)
        def execute_quotation_background():
            """Ejecuta el proceso completo en background"""
            task = task_manager.get_task(tracking_id)
            if not task:
                return

            try:
                task.start()
                task.update_progress("Iniciando cliente Odoo...")

                client = get_dev_client()
                steps = {}

                # PASO 1: Verificar/Crear Partner
                task.update_progress("Verificando partner...")
                email_normalizado = email.strip().lower()
                existing_partners = client.search_read(
                    "res.partner",
                    [("email", "=", email_normalizado)],
                    ["id", "name", "email", "phone"],
                    limit=1,
                )

                if existing_partners:
                    partner_id = existing_partners[0]["id"]
                    partner_full_name = existing_partners[0]["name"]
                    steps["partner"] = (
                        f"Partner existente: {partner_full_name} (ID: {partner_id})"
                    )
                else:
                    partner_values = {
                        "name": contact_name,
                        "email": email_normalizado,
                        "phone": phone,
                        "is_company": False,
                        "type": "contact",
                    }
                    # Agregar ciudad si se proporciona
                    if ciudad:
                        partner_values["city"] = ciudad

                    partner_id = client.create("res.partner", partner_values)
                    partner_full_name = partner_name
                    steps["partner"] = (
                        f"Nuevo partner creado: {partner_full_name} (ID: {partner_id})"
                    )

                task.update_progress("Partner verificado")

                # PASO 2: Asignar vendedor
                task.update_progress("Asignando vendedor...")
                assigned_user_id = user_id
                if not assigned_user_id:
                    assigned_user_id = client.get_salesperson_with_least_opportunities()
                    if assigned_user_id:
                        steps["user"] = (
                            f"Vendedor asignado automáticamente (ID: {assigned_user_id})"
                        )
                    else:
                        steps["user"] = "Sin vendedor asignado"
                else:
                    steps["user"] = f"Vendedor manual (ID: {assigned_user_id})"

                task.update_progress("Vendedor asignado")

                # PASO 3: Crear Lead
                task.update_progress("Creando lead...")
                lead_values = {
                    "name": lead_name,
                    "partner_name": partner_name,
                    "contact_name": contact_name,
                    "phone": phone,
                    "email_from": email_normalizado,
                    "type": "lead",
                    "partner_id": partner_id,
                }
                if assigned_user_id:
                    lead_values["user_id"] = assigned_user_id

                # Agregar campos personalizados
                if description:
                    lead_values["description"] = description

                # Auto-asignación de x_studio_producto (similar a core/api.py)
                if x_studio_producto:
                    lead_values["x_studio_producto"] = x_studio_producto
                elif products and len(products) > 0:
                    # Auto-asignar el primer producto del array
                    lead_values["x_studio_producto"] = products[0].get("product_id")
                elif product_id > 0:
                    # Legacy: asignar desde product_id
                    lead_values["x_studio_producto"] = product_id

                lead_id = client.create("crm.lead", lead_values)
                steps["lead"] = f"Lead creado: {lead_name} (ID: {lead_id})"
                task.update_progress("Lead creado")

                # PASO 4: Convertir a Oportunidad
                task.update_progress("Convirtiendo a oportunidad...")
                from datetime import datetime

                conversion_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                opportunity_values = {
                    "type": "opportunity",
                    "date_conversion": conversion_date,
                    "stage_id": 3,
                }
                if assigned_user_id:
                    opportunity_values["user_id"] = assigned_user_id

                client.write("crm.lead", lead_id, opportunity_values)
                steps["opportunity"] = f"Convertido a oportunidad (ID: {lead_id})"
                task.update_progress("Oportunidad creada")

                # PASO 5: Crear Sale Order
                task.update_progress("Creando cotización...")
                sale_values = {
                    "partner_id": partner_id,
                    "opportunity_id": lead_id,
                    "origin": lead_name,
                    "note": f"<p>Cotización desde oportunidad: {lead_name}</p>",
                }
                if assigned_user_id:
                    sale_values["user_id"] = assigned_user_id

                sale_order_id = client.create("sale.order", sale_values)
                sale_data = client.read("sale.order", sale_order_id, ["name"])
                sale_order_name = sale_data.get("name", f"S{sale_order_id}")
                steps["sale_order"] = (
                    f"Cotización: {sale_order_name} (ID: {sale_order_id})"
                )
                task.update_progress("Cotización creada")

                # PASO 6: Agregar productos (soporta múltiples productos)
                products_added = []

                # Determinar qué productos agregar
                products_to_add = []
                if products and len(products) > 0:
                    # Usar el nuevo formato de productos array
                    for p in products:
                        products_to_add.append(
                            {
                                "product_id": p.get("product_id"),
                                "qty": p.get("qty", 1.0),
                                "price": p.get("price", -1.0),
                            }
                        )
                elif product_id > 0:
                    # Legacy: usar product_id, product_qty, product_price
                    products_to_add.append(
                        {
                            "product_id": product_id,
                            "qty": product_qty,
                            "price": product_price,
                        }
                    )

                # Agregar cada producto
                for idx, product_data in enumerate(products_to_add, 1):
                    task.update_progress(
                        f"Agregando producto {idx}/{len(products_to_add)}..."
                    )

                    pid = product_data["product_id"]
                    qty = product_data["qty"]
                    price = product_data["price"]

                    line_values = {
                        "order_id": sale_order_id,
                        "product_id": pid,
                        "product_uom_qty": qty,
                    }

                    if price > 0:
                        line_values["price_unit"] = price
                        price_info = f"${price}"
                    else:
                        pricelist_id = 82
                        product_data_read = client.read(
                            "product.product", pid, ["name"]
                        )
                        product_name = product_data_read.get("name", "Unknown")

                        pricelist_items = client.search_read(
                            "product.pricelist.item",
                            [
                                ["pricelist_id", "=", pricelist_id],
                                ["product_id", "=", pid],
                            ],
                            ["fixed_price"],
                        )

                        if pricelist_items:
                            pricelist_price = pricelist_items[0].get("fixed_price", 0.0)
                            line_values["price_unit"] = pricelist_price
                            price_info = f"${pricelist_price}"
                        else:
                            product_data_full = client.read(
                                "product.product", pid, ["list_price"]
                            )
                            auto_price = product_data_full.get("list_price", 0.0)
                            line_values["price_unit"] = auto_price
                            price_info = f"${auto_price}"

                    line_id = client.create("sale.order.line", line_values)

                    # Agregar a la lista de productos agregados
                    products_added.append(
                        {
                            "product_id": pid,
                            "qty": qty,
                            "price": line_values.get("price_unit", 0.0),
                            "line_id": line_id,
                        }
                    )

                    if idx == 1:
                        steps["products"] = (
                            f"Producto 1: ID {pid} x {qty} = {price_info}"
                        )
                    else:
                        steps[
                            "products"
                        ] += f" | Producto {idx}: ID {pid} x {qty} = {price_info}"

                if products_added:
                    task.update_progress(
                        f"{len(products_added)} producto(s) agregado(s)"
                    )

                # Leer el lead actualizado para obtener los campos finales
                lead_final = client.read(
                    "crm.lead", lead_id, ["description", "x_studio_producto"]
                )

                # Enviar notificación SMS al vendedor
                notification_data = None
                try:
                    from core.whatsapp import sms_client
                    from core.helpers import get_user_whatsapp_number
                    from datetime import datetime

                    # Obtener el vendedor asignado al lead
                    lead_with_vendor = client.read("crm.lead", lead_id, ["user_id"])
                    vendor_id = None
                    if lead_with_vendor and lead_with_vendor.get("user_id"):
                        vendor_id = lead_with_vendor["user_id"][0]

                    if vendor_id:
                        # Obtener número del vendedor
                        vendor_sms = get_user_whatsapp_number(client, vendor_id)
                        if vendor_sms and vendor_sms.startswith("whatsapp:"):
                            vendor_sms = vendor_sms.replace("whatsapp:", "")
                        # Validar número (quitar si tiene X)
                        if vendor_sms and ("X" in vendor_sms or "x" in vendor_sms):
                            vendor_sms = None

                        # Preparar datos del lead para el mensaje
                        # Obtener nombres de productos para el mensaje
                        product_names = []
                        for prod in products_added:
                            try:
                                prod_info = client.read(
                                    "product.product", prod["product_id"], ["name"]
                                )
                                if prod_info:
                                    product_names.append(
                                        f"{prod_info['name']} (x{prod['qty']})"
                                    )
                            except:
                                product_names.append(
                                    f"Producto ID {prod['product_id']}"
                                )

                        lead_data_for_sms = {
                            "sale_order_name": sale_order_name,
                            "partner_name": partner_full_name,
                            "ciudad": (
                                ciudad if ciudad else "N/A"
                            ),  # Usar parámetro primero
                            "email": email,
                            "products": (
                                ", ".join(product_names) if product_names else "N/A"
                            ),
                        }

                        # Si no se proporcionó ciudad, intentar obtenerla del partner
                        if not ciudad:
                            try:
                                partner_data = client.read(
                                    "res.partner", partner_id, ["city"]
                                )
                                if partner_data and partner_data.get("city"):
                                    lead_data_for_sms["ciudad"] = partner_data["city"]
                            except Exception as e:
                                print(f"⚠️ No se pudo obtener ciudad del partner: {e}")

                        # Enviar SMS (reutilizando sms_client como lo hace message_notification)
                        sms_result = sms_client.send_handoff_notification(
                            user_phone=phone,
                            reason="Nueva cotización generada",
                            to_number=vendor_sms,
                            user_name=contact_name,
                            additional_context=f"Se generó la cotización {sale_order_name}",
                            lead_data=lead_data_for_sms,
                            assigned_user_id=vendor_id,
                        )

                        if sms_result["status"] == "success":
                            notification_data = {
                                "sent": True,
                                "method": "sms",
                                "message_sid": sms_result.get("message_sid"),
                                "sent_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "vendor_id": vendor_id,
                                "vendor_number": vendor_sms or "default",
                                "status": "success",
                            }
                            print(
                                f"✅ SMS de cotización enviado. SID: {sms_result.get('message_sid')}"
                            )
                        else:
                            notification_data = {
                                "sent": False,
                                "method": "sms",
                                "status": "error",
                                "error": sms_result.get("message"),
                                "vendor_id": vendor_id,
                            }
                            print(
                                f"⚠️ Error enviando SMS de cotización: {sms_result.get('message')}"
                            )
                    else:
                        print("⚠️ No se pudo determinar el vendedor para enviar SMS")
                        notification_data = {
                            "sent": False,
                            "method": "sms",
                            "status": "error",
                            "error": "No vendor assigned to lead",
                        }

                except Exception as sms_error:
                    print(f"❌ Error al enviar SMS de cotización: {sms_error}")
                    notification_data = {
                        "sent": False,
                        "method": "sms",
                        "status": "error",
                        "error": str(sms_error),
                    }

                # Resultado final con notificación
                result = {
                    "partner_id": partner_id,
                    "partner_name": partner_full_name,
                    "lead_id": lead_id,
                    "lead_name": lead_name,
                    "opportunity_id": lead_id,
                    "sale_order_id": sale_order_id,
                    "sale_order_name": sale_order_name,
                    "products_added": products_added,
                    "description": lead_final.get("description"),
                    "x_studio_producto": lead_final.get("x_studio_producto"),
                    "steps": steps,
                    "environment": "development",
                    "notification": notification_data,  # Agregar info de notificación
                }

                # Marcar como completado
                task.complete(result)

                # Actualizar log
                quotation_logger.update_quotation_log(
                    tracking_id=tracking_id,
                    output_data=result,
                    status="completed",
                    error=None,
                )

            except Exception as e:
                # Marcar como fallido
                error_msg = str(e)
                task.fail(error_msg)

                # Log de error
                quotation_logger.update_quotation_log(
                    tracking_id=tracking_id,
                    output_data=None,
                    status="failed",
                    error=error_msg,
                )

        # Lanzar thread
        thread = threading.Thread(target=execute_quotation_background, daemon=True)
        thread.start()

        # Retornar tracking_id inmediatamente
        return {
            "tracking_id": tracking_id,
            "status": "queued",
            "message": "Cotización en proceso. Usa dev_get_quotation_status() para consultar el estado.",
            "estimated_time": "20-30 segundos",
            "check_status_with": f"dev_get_quotation_status(tracking_id='{tracking_id}')",
        }

    @mcp.tool(
        name="dev_get_quotation_status",
        description="Consulta el estado de una cotización asíncrona usando su tracking_id. Retorna el estado actual (queued/processing/completed/failed) y el resultado si está disponible.",
    )
    def dev_get_quotation_status(tracking_id: str) -> dict:
        """
        Consulta el estado de una cotización creada con dev_create_quotation.

        Args:
            tracking_id: ID de seguimiento retornado por dev_create_quotation

        Returns:
            dict con status, progress, result (si completed), error (si failed)

        Ejemplo retorno (en proceso):
            {
                "tracking_id": "quot_abc123",
                "status": "processing",
                "progress": "Creando lead...",
                "created_at": "2025-12-22T10:48:40"
            }

        Ejemplo retorno (completado):
            {
                "tracking_id": "quot_abc123",
                "status": "completed",
                "result": {
                    "partner_id": 123,
                    "lead_id": 456,
                    "sale_order_id": 789,
                    "sale_order_name": "S00123",
                    "steps": {...}
                },
                "created_at": "2025-12-22T10:48:40",
                "updated_at": "2025-12-22T10:49:10"
            }
        """
        from core.tasks import task_manager

        task = task_manager.get_task(tracking_id)

        if not task:
            return {
                "tracking_id": tracking_id,
                "status": "not_found",
                "error": f"No se encontró tarea con tracking_id: {tracking_id}",
            }

        response = {
            "tracking_id": task.id,  # FIX: era task.task_id
            "status": (
                task.status.value if hasattr(task.status, "value") else str(task.status)
            ),
            "created_at": task.created_at.isoformat(),
        }

        # Agregar progreso si existe
        if task.progress:
            response["progress"] = task.progress

        # Agregar tiempo transcurrido
        response["elapsed_time"] = f"{task.elapsed_seconds():.2f}s"

        # Agregar completed_at si terminó
        if task.completed_at:
            response["completed_at"] = task.completed_at.isoformat()

        # Agregar resultado si completó exitosamente
        if task.status == TaskStatus.COMPLETED and task.result:
            response["result"] = task.result
            response["success"] = True  # Para ElevenLabs

        # Agregar error si falló
        if task.status == TaskStatus.FAILED and task.error:
            response["error"] = task.error
            response["success"] = False  # Para ElevenLabs

        return response
