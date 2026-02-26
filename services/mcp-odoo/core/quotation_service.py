"""
═══════════════════════════════════════════════════════════════════════
QUOTATION SERVICE - Core Business Logic
═══════════════════════════════════════════════════════════════════════

Este módulo centraliza toda la lógica de negocio para cotizaciones.
Tanto las herramientas MCP como los endpoints HTTP usan este servicio.

ARQUITECTURA:
    ┌─────────────────────────────────────────┐
    │   MCP Tools (tools/crm.py)              │
    │   - dev_create_quotation()              │
    │   - dev_update_lead_quotation()         │
    └──────────────┬──────────────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────────────┐
    │   HTTP Endpoints (server.py)            │
    │   - POST /api/quotation/create          │
    │   - POST /api/quotation/update-lead     │
    └──────────────┬──────────────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────────────┐
    │   QuotationService (este archivo)       │
    │   - create_from_scratch()               │
    │   - create_from_existing_lead()         │
    │   - _common_quotation_logic()           │
    └─────────────────────────────────────────┘

VENTAJAS:
- ✅ Cero duplicación de código
- ✅ Lógica de negocio centralizada
- ✅ Fácil de mantener y testear
- ✅ Reutilizable por múltiples interfaces

AUTOR: BravoMorteo
FECHA: Febrero 2026
═══════════════════════════════════════════════════════════════════════
"""

import uuid
import threading
from typing import Optional, List, Dict, Any
from datetime import datetime

from core.tasks import task_manager, TaskStatus
from core.logger import quotation_logger


class QuotationService:
    """
    Servicio centralizado para gestión de cotizaciones.

    Este servicio maneja toda la lógica de negocio para:
    1. Crear cotizaciones desde cero
    2. Crear cotizaciones desde leads existentes
    3. Actualizar leads y generar cotizaciones
    """

    def __init__(self, odoo_client):
        """
        Inicializa el servicio con un cliente de Odoo.

        Args:
            odoo_client: Instancia de OdooClient o DevOdooCRMClient
        """
        self.client = odoo_client

    def create_from_scratch(
        self,
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
        Crea una cotización completa desde cero (modo CREACIÓN).

        FLUJO:
        1. Crea/busca partner por email
        2. Asigna vendedor automáticamente
        3. Crea lead nuevo
        4. Convierte a oportunidad
        5. Crea orden de venta
        6. Agrega productos
        7. Envía notificación

        Args:
            partner_name: Nombre del cliente/empresa
            contact_name: Nombre del contacto
            email: Email del contacto
            phone: Teléfono del contacto
            lead_name: Nombre del lead/oportunidad
            ciudad: Ciudad del contacto (opcional)
            user_id: ID del vendedor (0 = asignación automática)
            product_id: ID del producto (LEGACY)
            product_qty: Cantidad (LEGACY)
            product_price: Precio manual (LEGACY)
            products: Lista de productos [{"product_id": int, "qty": float, "price": float}]
            description: Descripción del lead
            x_studio_producto: Producto principal (Many2one)

        Returns:
            dict con tracking_id, status, message
        """
        # Generar tracking_id
        tracking_id = f"quot_new_{uuid.uuid4().hex[:12]}"

        # Preparar parámetros
        params = {
            "mode": "create",
            "partner_name": partner_name,
            "contact_name": contact_name,
            "email": email,
            "phone": phone,
            "lead_name": lead_name,
            "ciudad": ciudad,
            "user_id": user_id,
            "product_id": product_id,
            "product_qty": product_qty,
            "product_price": product_price,
            "products": products,
            "description": description,
            "x_studio_producto": x_studio_producto,
        }

        # Crear tarea
        task_manager.create_task(tracking_id, params)

        # Log inicial
        quotation_logger.log_quotation(
            tracking_id=tracking_id,
            input_data=params,
            status="queued",
            mode="create",
        )

        print(f"🆔 Tracking ID: {tracking_id}")
        print(f"📋 Modo: CREACIÓN")

        # Ejecutar en background
        thread = threading.Thread(
            target=self._execute_create_from_scratch,
            args=(tracking_id, params),
            daemon=True,
        )
        thread.start()

        return {
            "tracking_id": tracking_id,
            "status": "queued",
            "mode": "create",
            "message": "Creando cotización desde cero. Usa dev_get_quotation_status() para consultar.",
            "estimated_time": "20-30 segundos",
            "check_status_with": f"dev_get_quotation_status(tracking_id='{tracking_id}')",
        }

    def create_from_existing_lead(
        self,
        lead_id: int,
        products: Optional[List[dict]] = None,
        product_id: int = 0,
        product_qty: float = 1.0,
        product_price: float = -1.0,
        update_lead_data: Optional[dict] = None,
        description: Optional[str] = None,
        x_studio_producto: Optional[int] = None,
    ) -> dict:
        """
        Crea una cotización desde un lead EXISTENTE (modo ACTUALIZACIÓN).

        FLUJO:
        1. Lee lead existente
        2. Actualiza datos del lead (opcional)
        3. Convierte a oportunidad (si no lo es)
        4. Crea orden de venta
        5. Agrega productos
        6. Envía notificación

        Args:
            lead_id: ID del lead existente (OBLIGATORIO)
            products: Lista de productos
            product_id: ID del producto (LEGACY)
            product_qty: Cantidad (LEGACY)
            product_price: Precio manual (LEGACY)
            update_lead_data: Diccionario con campos a actualizar
                Ejemplo: {"description": "...", "city": "CDMX", "priority": 3}
            description: Descripción adicional
            x_studio_producto: Producto principal

        Returns:
            dict con tracking_id, status, message
        """
        # Validar lead_id
        if not lead_id or lead_id <= 0:
            raise ValueError("lead_id es obligatorio y debe ser mayor a 0")

        # Generar tracking_id
        tracking_id = f"quot_upd_{uuid.uuid4().hex[:12]}"

        # Preparar parámetros
        params = {
            "mode": "update",
            "lead_id": lead_id,
            "products": products,
            "product_id": product_id,
            "product_qty": product_qty,
            "product_price": product_price,
            "update_lead_data": update_lead_data,
            "description": description,
            "x_studio_producto": x_studio_producto,
        }

        # Crear tarea
        task_manager.create_task(tracking_id, params)

        # Log inicial
        quotation_logger.log_quotation(
            tracking_id=tracking_id,
            input_data=params,
            status="queued",
            mode="update",
        )

        print(f"🆔 Tracking ID: {tracking_id}")
        print(f"📋 Modo: ACTUALIZACIÓN (Lead ID: {lead_id})")

        # Ejecutar en background
        thread = threading.Thread(
            target=self._execute_create_from_existing_lead,
            args=(tracking_id, params, lead_id),
            daemon=True,
        )
        thread.start()

        return {
            "tracking_id": tracking_id,
            "status": "queued",
            "mode": "update",
            "lead_id": lead_id,
            "message": f"Actualizando lead {lead_id} y creando cotización. Usa dev_get_quotation_status() para consultar.",
            "estimated_time": "15-25 segundos",
            "check_status_with": f"dev_get_quotation_status(tracking_id='{tracking_id}')",
        }

    # ═══════════════════════════════════════════════════════════════════
    # MÉTODOS PRIVADOS - EJECUCIÓN EN BACKGROUND
    # ═══════════════════════════════════════════════════════════════════

    def _execute_create_from_scratch(self, tracking_id: str, params: dict):
        """Ejecuta creación desde cero en background."""
        task = task_manager.get_task(tracking_id)
        if not task:
            return

        try:
            task.start()
            task.update_progress("Iniciando creación desde cero...")

            # Importar normalize_email
            from tools.crm import normalize_email

            # Verificar conexión con retry
            self._verify_odoo_connection()

            steps = {}

            # PASO 1: Crear/buscar partner
            task.update_progress("Verificando partner...")
            email_normalizado = normalize_email(params["email"])

            existing_partners = self.client.search_read(
                "res.partner",
                [("email", "=", email_normalizado)],
                ["id", "name"],
                limit=1,
            )

            if existing_partners:
                partner_id = existing_partners[0]["id"]
                partner_name = existing_partners[0]["name"]
                steps["partner"] = (
                    f"Partner existente: {partner_name} (ID: {partner_id})"
                )
            else:
                partner_values = {
                    "name": params["contact_name"],
                    "email": email_normalizado,
                    "phone": params["phone"],
                    "is_company": False,
                    "type": "contact",
                }
                if params.get("ciudad"):
                    partner_values["city"] = params["ciudad"]

                partner_id = self.client.create("res.partner", partner_values)
                partner_name = params["partner_name"]
                steps["partner"] = (
                    f"Nuevo partner creado: {partner_name} (ID: {partner_id})"
                )

            # PASO 2: Asignar vendedor
            task.update_progress("Asignando vendedor...")
            user_id = params.get("user_id", 0)
            if not user_id:
                user_id = self.client.get_salesperson_with_least_opportunities()
                steps["user"] = f"Vendedor asignado automáticamente (ID: {user_id})"
            else:
                steps["user"] = f"Vendedor manual (ID: {user_id})"

            # PASO 3: Crear lead
            task.update_progress("Creando lead...")
            lead_values = {
                "name": params["lead_name"],
                "partner_name": params["partner_name"],
                "contact_name": params["contact_name"],
                "phone": params["phone"],
                "email_from": email_normalizado,
                "type": "lead",
                "partner_id": partner_id,
            }
            if user_id:
                lead_values["user_id"] = user_id
            if params.get("description"):
                lead_values["description"] = params["description"]

            # Auto-asignación de x_studio_producto
            if params.get("x_studio_producto"):
                lead_values["x_studio_producto"] = params["x_studio_producto"]
            elif params.get("products") and len(params["products"]) > 0:
                lead_values["x_studio_producto"] = params["products"][0].get(
                    "product_id"
                )
            elif params.get("product_id", 0) > 0:
                lead_values["x_studio_producto"] = params["product_id"]

            lead_id = self.client.create("crm.lead", lead_values)
            lead_name = params["lead_name"]
            steps["lead"] = f"Lead creado: {lead_name} (ID: {lead_id})"

            # PASO 4: Convertir a oportunidad
            task.update_progress("Convirtiendo a oportunidad...")
            conversion_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            opportunity_values = {
                "type": "opportunity",
                "date_conversion": conversion_date,
                "stage_id": 3,
            }
            if user_id:
                opportunity_values["user_id"] = user_id

            self.client.write("crm.lead", lead_id, opportunity_values)
            steps["opportunity"] = f"Convertido a oportunidad (ID: {lead_id})"

            # PASO 5-7: Lógica común (orden de venta + productos + notificación)
            result = self._common_quotation_logic(
                task=task,
                tracking_id=tracking_id,
                lead_id=lead_id,
                lead_name=lead_name,
                partner_id=partner_id,
                partner_name=partner_name,
                user_id=user_id,
                params=params,
                steps=steps,
                mode="create",
            )

            # Completar tarea
            task.complete(result)
            quotation_logger.update_quotation_log(
                tracking_id=tracking_id,
                output_data=result,
                status="completed",
                error=None,
            )
            print(f"✅ Cotización creada: {tracking_id}")

        except Exception as e:
            self._handle_error(task, tracking_id, params, e)

    def _execute_create_from_existing_lead(
        self, tracking_id: str, params: dict, lead_id: int
    ):
        """Ejecuta creación desde lead existente en background."""
        task = task_manager.get_task(tracking_id)
        if not task:
            return

        try:
            task.start()
            task.update_progress("Iniciando desde lead existente...")

            # Verificar conexión
            self._verify_odoo_connection()

            steps = {}

            # PASO 1: Leer lead existente
            task.update_progress("Leyendo lead existente...")
            lead = self.client.read(
                "crm.lead",
                lead_id,
                [
                    "id",
                    "name",
                    "type",
                    "partner_id",
                    "user_id",
                    "stage_id",
                    "contact_name",
                    "email_from",
                    "phone",
                    "city",
                    "description",
                    "x_studio_producto",
                ],
            )

            if not lead:
                raise ValueError(f"No se encontró el lead con ID {lead_id}")

            steps["read_lead"] = f"Lead encontrado: {lead.get('name', 'Sin nombre')}"
            print(f"✅ Lead: {lead.get('name')} (ID: {lead_id})")

            # PASO 2: Actualizar datos del lead ANTES de verificar partner (opcional)
            update_lead_data = params.get("update_lead_data")
            if update_lead_data:
                task.update_progress("Actualizando lead...")
                update_values = {
                    k: v
                    for k, v in update_lead_data.items()
                    if v is not None and k != "partner_name"
                }

                # Si viene partner_name, buscar o crear el partner
                if (
                    "partner_name" in update_lead_data
                    and update_lead_data["partner_name"]
                ):
                    partner_name_to_create = update_lead_data["partner_name"]

                    # Buscar partner existente
                    existing_partners = self.client.search_read(
                        "res.partner",
                        [("name", "=", partner_name_to_create)],
                        ["id", "name"],
                        limit=1,
                    )

                    if existing_partners:
                        new_partner_id = existing_partners[0]["id"]
                        print(
                            f"✅ Partner encontrado: {partner_name_to_create} (ID: {new_partner_id})"
                        )
                    else:
                        # Crear nuevo partner
                        partner_values = {"name": partner_name_to_create}
                        if "email_from" in update_lead_data:
                            partner_values["email"] = update_lead_data["email_from"]
                        if "phone" in update_lead_data:
                            partner_values["phone"] = update_lead_data["phone"]
                        if "city" in update_lead_data:
                            partner_values["city"] = update_lead_data["city"]

                        new_partner_id = self.client.create(
                            "res.partner", partner_values
                        )
                        print(
                            f"✅ Partner creado: {partner_name_to_create} (ID: {new_partner_id})"
                        )

                    # Asignar partner al lead
                    update_values["partner_id"] = new_partner_id

                if update_values:
                    self.client.write("crm.lead", lead_id, update_values)
                    steps["update_lead"] = (
                        f"Campos actualizados: {list(update_values.keys())}"
                    )
                    print(f"✅ Lead actualizado: {list(update_values.keys())}")

                    # Re-leer el lead para obtener el partner actualizado
                    lead = self.client.read(
                        "crm.lead",
                        lead_id,
                        [
                            "name",
                            "partner_id",
                            "user_id",
                            "type",
                            "stage_id",
                            "email_from",
                            "phone",
                            "city",
                            "description",
                            "x_studio_producto",
                        ],
                    )

            # Extraer datos (después de la actualización)
            partner_info = lead.get("partner_id")
            partner_id = partner_info[0] if partner_info else None
            user_info = lead.get("user_id")
            user_id = user_info[0] if user_info else None
            lead_name = lead.get("name", "Cotización desde lead existente")

            # Si no hay user_id asignado, asignar uno automáticamente (balanceo de carga)
            if not user_id:
                print(f"⚠️ Lead sin vendedor asignado, asignando automáticamente...")
                from core.helpers import get_available_vendor_with_least_leads

                user_id = get_available_vendor_with_least_leads(self.client)
                if user_id:
                    # Asignar vendedor al lead
                    self.client.write("crm.lead", lead_id, {"user_id": user_id})
                    print(f"✅ Vendedor asignado automáticamente: {user_id}")
                else:
                    print(f"⚠️ No se pudo asignar vendedor automáticamente")

            if not partner_id:
                raise ValueError(f"El lead {lead_id} no tiene un partner asociado.")

            # Obtener partner_name
            partner_data = self.client.read("res.partner", partner_id, ["name"])
            partner_name = partner_data.get("name", "Sin nombre")

            # PASO 3: Convertir a oportunidad (si no lo es)
            if lead.get("type") != "opportunity":
                task.update_progress("Convirtiendo a oportunidad...")
                opportunity_values = {
                    "type": "opportunity",
                    "stage_id": 1,
                }
                if params.get("description"):
                    opportunity_values["description"] = params["description"]

                # Asignar x_studio_producto
                if params.get("x_studio_producto"):
                    opportunity_values["x_studio_producto"] = params[
                        "x_studio_producto"
                    ]
                elif params.get("products") and len(params["products"]) > 0:
                    opportunity_values["x_studio_producto"] = params["products"][0].get(
                        "product_id"
                    )
                elif params.get("product_id", 0) > 0:
                    opportunity_values["x_studio_producto"] = params["product_id"]

                self.client.write("crm.lead", lead_id, opportunity_values)
                steps["convert_to_opportunity"] = "Convertido a oportunidad"
                print(f"✅ Convertido a oportunidad")
            else:
                steps["convert_to_opportunity"] = "Ya era oportunidad"

            # PASO 4-6: Lógica común (orden de venta + productos + notificación)
            result = self._common_quotation_logic(
                task=task,
                tracking_id=tracking_id,
                lead_id=lead_id,
                lead_name=lead_name,
                partner_id=partner_id,
                partner_name=partner_name,
                user_id=user_id,
                params=params,
                steps=steps,
                mode="update",
                update_lead_data=update_lead_data,
            )

            # Completar tarea
            task.complete(result)
            quotation_logger.update_quotation_log(
                tracking_id=tracking_id,
                output_data=result,
                status="completed",
                error=None,
            )
            print(f"✅ Cotización desde lead existente: {tracking_id}")

        except Exception as e:
            self._handle_error(task, tracking_id, params, e)

    def _common_quotation_logic(
        self,
        task,
        tracking_id: str,
        lead_id: int,
        lead_name: str,
        partner_id: int,
        partner_name: str,
        user_id: Optional[int],
        params: dict,
        steps: dict,
        mode: str,
        update_lead_data: Optional[dict] = None,
    ) -> dict:
        """
        Lógica común para ambos modos: crear orden de venta + productos + notificación.

        Esta función evita duplicar código entre los dos flujos.
        """
        # PASO: Crear orden de venta
        task.update_progress("Creando orden de venta...")
        sale_values = {
            "partner_id": partner_id,
            "opportunity_id": lead_id,
            "website_id": 1,  # Fix: Especificar website_id para evitar error de singleton
        }
        if mode == "create":
            sale_values["origin"] = lead_name
            sale_values["note"] = f"<p>Cotización desde oportunidad: {lead_name}</p>"
        if user_id:
            sale_values["user_id"] = user_id

        sale_order_id = self.client.create("sale.order", sale_values)
        sale_data = self.client.read("sale.order", sale_order_id, ["name"])
        sale_order_name = sale_data.get("name", f"S{sale_order_id}")
        steps["sale_order"] = f"Orden de venta: {sale_order_name} (ID: {sale_order_id})"

        # PASO: Agregar productos
        task.update_progress("Agregando productos...")
        products_added = self._add_products_to_order(sale_order_id, params)
        steps["add_products"] = f"{len(products_added)} productos agregados"

        # PASO: Leer lead final
        lead_final = self.client.read(
            "crm.lead",
            lead_id,
            [
                "name",
                "description",
                "x_studio_producto",
                "partner_id",
                "phone",
                "contact_name",
            ],
        )

        # PASO: Enviar notificación
        task.update_progress("Enviando notificación...")
        notification_data = self._send_notification(
            lead_id,
            user_id,
            sale_order_name,
            partner_name,
            products_added,
            params,
            lead_final,
        )

        # Resultado final
        result = {
            "mode": mode,
            "partner_id": partner_id,
            "partner_name": partner_name,
            "lead_id": lead_id,
            "lead_name": lead_name,
            "opportunity_id": lead_id,
            "sale_order_id": sale_order_id,
            "sale_order_name": sale_order_name,
            "products_added": products_added,
            "updated_fields": list(update_lead_data.keys()) if update_lead_data else [],
            "description": lead_final.get("description"),
            "x_studio_producto": lead_final.get("x_studio_producto"),
            "steps": steps,
            "environment": "development",
            "notification": notification_data,
        }

        return result

    def _add_products_to_order(self, sale_order_id: int, params: dict) -> List[dict]:
        """Agrega productos a la orden de venta."""
        products_added = []
        products_to_add = []

        # Determinar productos
        if params.get("products"):
            products_to_add = params["products"]
        elif params.get("product_id", 0) > 0:
            products_to_add = [
                {
                    "product_id": params["product_id"],
                    "qty": params.get("product_qty", 1.0),
                    "price": params.get("product_price", -1.0),
                }
            ]

        # Agregar cada producto
        for idx, prod in enumerate(products_to_add, 1):
            prod_id = prod.get("product_id")
            qty = prod.get("qty", 1.0)
            price = prod.get("price", -1.0)

            if not prod_id:
                continue

            line_values = {
                "order_id": sale_order_id,
                "product_id": prod_id,
                "product_uom_qty": qty,
            }

            # Precio manual o automático
            if price > 0:
                line_values["price_unit"] = price
            else:
                # Obtener precio de pricelist
                product_data = self.client.read(
                    "product.product", prod_id, ["list_price", "name"]
                )
                line_values["price_unit"] = product_data.get("list_price", 0.0)

            line_id = self.client.create("sale.order.line", line_values)
            product_info = self.client.read("product.product", prod_id, ["name"])

            products_added.append(
                {
                    "line_id": line_id,
                    "product_id": prod_id,
                    "product_name": product_info.get("name", f"Producto {prod_id}"),
                    "qty": qty,
                    "price": line_values.get("price_unit", 0.0),
                }
            )

            print(f"   ✅ Producto: {product_info.get('name')} (qty: {qty})")

        return products_added

    def _send_notification(
        self,
        lead_id: int,
        user_id: Optional[int],
        sale_order_name: str,
        partner_name: str,
        products_added: List[dict],
        params: dict,
        lead_final: dict,
    ) -> dict:
        """Envía notificación WhatsApp al vendedor."""
        notification_data = {"sent": False}

        try:
            from core.whatsapp import sms_client
            from core.helpers import get_user_whatsapp_number

            if user_id:
                vendor_sms = get_user_whatsapp_number(self.client, user_id)
                if vendor_sms and vendor_sms.startswith("whatsapp:"):
                    vendor_sms = vendor_sms.replace("whatsapp:", "")

                if vendor_sms and ("X" not in vendor_sms and "x" not in vendor_sms):
                    # Preparar mensaje
                    products_summary = "\n".join(
                        [f"• {p['product_name']} (x{p['qty']})" for p in products_added]
                    )

                    lead_data_for_sms = {
                        "sale_order_name": sale_order_name,
                        "partner_name": partner_name,
                        "ciudad": params.get("ciudad", "N/A"),
                        "email": params.get(
                            "email", lead_final.get("email_from", "N/A")
                        ),
                        "products": products_summary or "N/A",
                    }

                    user_phone = params.get("phone", lead_final.get("phone", "N/A"))
                    user_name = params.get(
                        "contact_name", lead_final.get("contact_name", "N/A")
                    )

                    sms_result = sms_client.send_handoff_notification(
                        user_phone=user_phone,
                        reason="Nueva cotización generada",
                        to_number=vendor_sms,
                        user_name=user_name,
                        additional_context=f"Se generó la cotización {sale_order_name}",
                        lead_data=lead_data_for_sms,
                        assigned_user_id=user_id,
                    )

                    if sms_result.get("status") == "success":
                        notification_data = {
                            "sent": True,
                            "method": "whatsapp",
                            "message_sid": sms_result.get("message_sid"),
                            "status": "success",
                        }
                        print(f"✅ WhatsApp enviado: {sms_result.get('message_sid')}")
                    else:
                        notification_data = {
                            "sent": False,
                            "method": "whatsapp",
                            "status": "error",
                            "error": sms_result.get("message"),
                        }
        except Exception as e:
            print(f"⚠️ Error en notificación: {e}")
            notification_data = {
                "sent": False,
                "method": "whatsapp",
                "status": "error",
                "error": str(e),
            }

        return notification_data

    def _verify_odoo_connection(self):
        """Verifica la conexión con Odoo con reintentos."""
        max_retries = 4
        retry_delays = [3, 5, 10]

        for attempt in range(max_retries):
            try:
                self.client.search_read("res.partner", [], ["id"], limit=1)
                if attempt > 0:
                    print(f"✅ Conexión Odoo exitosa (intento {attempt + 1})")
                return
            except Exception as conn_error:
                if attempt < max_retries - 1:
                    delay = retry_delays[attempt] if attempt < len(retry_delays) else 10
                    print(
                        f"⚠️ Intento {attempt + 1}/{max_retries} falló, esperando {delay}s..."
                    )
                    import time

                    time.sleep(delay)
                else:
                    raise Exception(
                        f"Odoo connection failed after {max_retries} attempts: {str(conn_error)[:200]}"
                    )

    def _handle_error(self, task, tracking_id: str, params: dict, error: Exception):
        """Maneja errores de forma centralizada."""
        import traceback

        error_msg = str(error)
        error_details = {
            "error_type": type(error).__name__,
            "error_message": error_msg[:500],
            "traceback": traceback.format_exc()[:1000],
        }

        print(f"❌ Error en cotización {tracking_id}:")
        print(f"   Tipo: {error_details['error_type']}")
        print(f"   Mensaje: {error_details['error_message']}")

        if error_msg.startswith("<!doctype html") or error_msg.startswith("<!DOCTYPE"):
            error_msg = "Odoo server error (502/HTML response). Server may be down."

        task.fail(error_msg)

        quotation_logger.update_quotation_log(
            tracking_id=tracking_id,
            output_data=None,
            status="failed",
            error=error_msg,
        )
