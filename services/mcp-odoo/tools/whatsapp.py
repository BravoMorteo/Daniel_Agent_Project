"""
MCP Tool para SMS Handoff
Permite enviar notificaciones de handoff a vendedores por SMS
"""

from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

from core.whatsapp import sms_client
from core.helpers import get_user_whatsapp_number
from core.logger import quotation_logger


class HandoffResult(BaseModel):
    """Modelo para el resultado del handoff"""

    status: str
    message: str
    message_sid: Optional[str] = None
    to_number: Optional[str] = None
    from_number: Optional[str] = None
    assigned_user_id: Optional[int] = None


def register(mcp, deps: dict):
    """
    Registra la herramienta MCP para WhatsApp Handoff.

    Esta herramienta permite enviar notificaciones al vendedor
    cuando un cliente solicita atención humana.
    """

    # Cliente de DESARROLLO - lazy loading
    dev_client = None

    def get_dev_client():
        """Inicializa el cliente de desarrollo solo cuando se necesita."""
        nonlocal dev_client
        if dev_client is None:
            from tools.crm import DevOdooCRMClient

            dev_client = DevOdooCRMClient()
        return dev_client

    @mcp.tool(
        name="message_notification",
        description="Envía notificación al vendedor por SMS cuando un cliente solicita atención humana. Si hay lead_id o sale_order_id, usa ese vendedor. Si no, asigna al vendedor con menos leads.",
    )
    def message_notification(
        user_phone: str,
        reason: str,
        user_name: Optional[str] = None,
        conversation_id: Optional[str] = None,
        additional_context: Optional[str] = None,
        lead_id: Optional[int] = None,
        sale_order_id: Optional[int] = None,
    ) -> HandoffResult:
        """
        Envía una notificación de handoff al vendedor por WhatsApp.

        Lógica de asignación de vendedor:
        1. Si se proporciona lead_id: usa el vendedor asignado a ese lead
        2. Si se proporciona sale_order_id: usa el vendedor asignado a esa orden
        3. Si no hay lead ni orden: usa la lógica de "vendedor con menos leads"

        Args:
            user_phone: Teléfono del cliente en formato internacional (ej: +5215512345678)
            reason: Motivo del handoff (ej: "Cliente desea hablar con vendedor")
            user_name: Nombre del cliente (opcional)
            conversation_id: ID de la conversación en ElevenLabs (opcional)
            additional_context: Contexto adicional de la conversación (opcional)
            lead_id: ID del lead/oportunidad en Odoo (opcional)
            sale_order_id: ID de la orden de venta en Odoo (opcional)

        Returns:
            HandoffResult con el estado de la notificación enviada

        Raises:
            ValueError: Si el servicio de SMS no está configurado
            Exception: Si hay error al enviar el mensaje
        """
        print(f"[MCP Tool] sms_handoff llamado para {user_phone} - {reason}")

        # Verificar configuración
        if not sms_client.is_configured():
            error_msg = (
                "SMS service not configured. Check TWILIO_* environment variables."
            )
            print(f"[MCP Tool] ❌ {error_msg}")
            raise ValueError(error_msg)

        # Determinar el vendedor a quien enviar
        assigned_user_id = None
        vendor_sms = None

        client = get_dev_client()

        # Caso 1: Hay lead_id, obtener el vendedor del lead
        if lead_id:
            print(f"[MCP Tool] 📋 Lead ID proporcionado: {lead_id}")
            try:
                lead = client.read("crm.lead", lead_id, ["user_id"])
                if lead and lead.get("user_id"):
                    # El lead tiene vendedor asignado, usar ese
                    assigned_user_id = lead["user_id"][0]
                    print(
                        f"[MCP Tool] ✅ Vendedor ya asignado en lead: {assigned_user_id}"
                    )
                else:
                    # El lead NO tiene vendedor, aplicar lógica de balanceo
                    print(
                        f"[MCP Tool] ⚠️  Lead sin vendedor asignado, aplicando lógica de balanceo..."
                    )
            except Exception as e:
                print(f"[MCP Tool] ⚠️  Error leyendo lead: {e}")

        # Caso 2: Hay sale_order_id, obtener el vendedor de la orden
        elif sale_order_id:
            print(f"[MCP Tool] 📋 Sale Order ID proporcionado: {sale_order_id}")
            try:
                order = client.read("sale.order", sale_order_id, ["user_id"])
                if order and order.get("user_id"):
                    # La orden tiene vendedor asignado, usar ese
                    assigned_user_id = order["user_id"][0]
                    print(
                        f"[MCP Tool] ✅ Vendedor ya asignado en orden: {assigned_user_id}"
                    )
                else:
                    # La orden NO tiene vendedor, aplicar lógica de balanceo
                    print(
                        f"[MCP Tool] ⚠️  Orden sin vendedor asignado, aplicando lógica de balanceo..."
                    )
            except Exception as e:
                print(f"[MCP Tool] ⚠️  Error leyendo orden: {e}")

        # Caso 3: No hay vendedor asignado todavía, usar lógica de "vendedor con menos leads"
        if not assigned_user_id:
            print(
                f"[MCP Tool] 🔍 Aplicando lógica de balanceo (vendedor con menos leads)..."
            )
            try:
                assigned_user_id = client.get_salesperson_with_least_opportunities()
                if assigned_user_id:
                    print(
                        f"[MCP Tool] ✅ Vendedor seleccionado por balanceo: {assigned_user_id}"
                    )
                else:
                    print(
                        f"[MCP Tool] ⚠️  No se encontró vendedor disponible en el equipo"
                    )
            except Exception as e:
                print(f"[MCP Tool] ❌ Error en lógica de balanceo: {e}")

        # Obtener el número SMS del vendedor (reutilizamos la función pero para SMS)
        if assigned_user_id:
            vendor_sms = get_user_whatsapp_number(client, assigned_user_id)
            # Limpiar prefijo whatsapp: si existe
            if vendor_sms and vendor_sms.startswith("whatsapp:"):
                vendor_sms = vendor_sms.replace("whatsapp:", "")
            # Validar que el número no tenga 'X' (número oculto por privacidad en dev)
            if vendor_sms and ("X" in vendor_sms or "x" in vendor_sms):
                print(
                    f"[MCP Tool] ⚠️  Número del vendedor oculto por privacidad, usando default"
                )
                vendor_sms = None
            if not vendor_sms:
                print(
                    f"[MCP Tool] ⚠️  No se pudo obtener número SMS válido del vendedor {assigned_user_id}, usando default"
                )
        else:
            print(f"[MCP Tool] ⚠️  No se asignó vendedor, usando número default")

        # Si hay lead_id, intentar obtener datos de la cotización para el mensaje
        lead_data = None
        if lead_id:
            try:
                print(
                    f"[MCP Tool] 📋 Obteniendo datos de cotización del lead {lead_id}..."
                )
                # Leer datos del lead y orden de venta asociada
                lead_info = client.search_read(
                    "crm.lead",
                    [["id", "=", lead_id]],
                    ["name", "partner_id", "email_from", "order_ids"],
                    limit=1,
                )

                if lead_info and lead_info[0].get("order_ids"):
                    order_ids = lead_info[0]["order_ids"]
                    if order_ids:
                        # Obtener la orden de venta
                        order_info = client.read(
                            "sale.order",
                            order_ids[0],
                            ["name", "partner_id", "order_line"],
                        )

                        if order_info:
                            # Obtener productos de la orden
                            order_lines = order_info.get("order_line", [])
                            product_names = []

                            if order_lines:
                                for line_id in order_lines:
                                    try:
                                        line_info = client.read(
                                            "sale.order.line",
                                            line_id,
                                            ["product_id", "product_uom_qty"],
                                        )
                                        if line_info and line_info.get("product_id"):
                                            prod_name = line_info["product_id"][1]
                                            prod_qty = line_info.get(
                                                "product_uom_qty", 1
                                            )
                                            product_names.append(
                                                f"{prod_name} (x{prod_qty})"
                                            )
                                    except Exception as e:
                                        print(
                                            f"[MCP Tool] ⚠️  Error leyendo línea de orden: {e}"
                                        )

                            # Preparar lead_data para el mensaje
                            partner_name = (
                                order_info.get("partner_id", [False, "N/A"])[1]
                                if order_info.get("partner_id")
                                else "N/A"
                            )

                            lead_data = {
                                "sale_order_name": order_info.get("name", "N/A"),
                                "partner_name": partner_name,
                                "ciudad": "N/A",
                                "email": lead_info[0].get("email_from", "N/A"),
                                "products": (
                                    ", ".join(product_names) if product_names else "N/A"
                                ),
                            }
                            print(
                                f"[MCP Tool] ✅ Datos de cotización obtenidos: {order_info.get('name')}"
                            )

            except Exception as e:
                print(f"[MCP Tool] ⚠️  Error obteniendo datos de cotización: {e}")
                # Continuar sin lead_data

        # Enviar notificación
        result = sms_client.send_handoff_notification(
            user_phone=user_phone,
            reason=reason,
            to_number=vendor_sms,  # Puede ser None, usará default
            user_name=user_name,
            conversation_id=conversation_id,
            additional_context=additional_context,
            lead_data=lead_data,  # Incluir datos de cotización si existen
            assigned_user_id=assigned_user_id,  # Pasar ID del vendedor para el mensaje
        )

        # Verificar resultado
        if result["status"] == "error":
            error_msg = f"Failed to send SMS: {result['message']}"
            print(f"[MCP Tool] ❌ {error_msg}")

            # Log error handoff
            try:
                handoff_id = (
                    f"sms_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"
                )
                quotation_logger.log_sms_handoff(
                    handoff_id=handoff_id,
                    user_phone=user_phone,
                    reason=reason,
                    user_name=user_name,
                    conversation_id=conversation_id,
                    additional_context=additional_context,
                    lead_id=lead_id,
                    sale_order_id=sale_order_id,
                    assigned_user_id=assigned_user_id,
                    vendor_sms=vendor_sms,
                    message_sid=None,
                    status="error",
                    error=result.get("message"),
                )
            except Exception as log_err:
                print(f"[MCP Tool] ⚠️  Error logging failed handoff: {log_err}")

            raise Exception(error_msg)

        print(
            f"[MCP Tool] ✅ SMS handoff sent successfully. SID: {result.get('message_sid')}"
        )

        # Log successful handoff
        try:
            handoff_id = (
                f"sms_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"
            )
            log_path = quotation_logger.log_sms_handoff(
                handoff_id=handoff_id,
                user_phone=user_phone,
                reason=reason,
                user_name=user_name,
                conversation_id=conversation_id,
                additional_context=additional_context,
                lead_id=lead_id,
                sale_order_id=sale_order_id,
                assigned_user_id=assigned_user_id,
                vendor_sms=vendor_sms,
                message_sid=result.get("message_sid"),
                status="success",
            )
            print(f"[MCP Tool] 📝 Handoff logged to: {log_path}")
        except Exception as log_err:
            print(f"[MCP Tool] ⚠️  Error logging successful handoff: {log_err}")

        return HandoffResult(
            status="success",
            message="Notificación SMS enviada al vendedor exitosamente",
            message_sid=result.get("message_sid"),
            to_number=result.get("to"),
            from_number=result.get("from"),
            assigned_user_id=assigned_user_id,
        )
