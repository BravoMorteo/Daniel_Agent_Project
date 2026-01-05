"""
MCP Tool para WhatsApp Handoff
Permite enviar notificaciones de handoff a vendedores por WhatsApp
"""

from typing import Optional
from pydantic import BaseModel

from core.whatsapp import whatsapp_client
from core.helpers import get_user_whatsapp_number


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
        name="whatsapp_handoff",
        description="Envía notificación al vendedor por WhatsApp cuando un cliente solicita atención humana. Si hay lead_id o sale_order_id, usa ese vendedor. Si no, asigna al vendedor con menos leads.",
    )
    def whatsapp_handoff(
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
            ValueError: Si el servicio de WhatsApp no está configurado
            Exception: Si hay error al enviar el mensaje
        """
        print(f"[MCP Tool] whatsapp_handoff llamado para {user_phone} - {reason}")

        # Verificar configuración
        if not whatsapp_client.is_configured():
            error_msg = (
                "WhatsApp service not configured. Check TWILIO_* environment variables."
            )
            print(f"[MCP Tool] ❌ {error_msg}")
            raise ValueError(error_msg)

        # Determinar el vendedor a quien enviar
        assigned_user_id = None
        vendor_whatsapp = None

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

        # Obtener el número de WhatsApp del vendedor
        if assigned_user_id:
            vendor_whatsapp = get_user_whatsapp_number(client, assigned_user_id)
            if not vendor_whatsapp:
                print(
                    f"[MCP Tool] ⚠️  No se pudo obtener WhatsApp del vendedor {assigned_user_id}, usando default"
                )
        else:
            print(f"[MCP Tool] ⚠️  No se asignó vendedor, usando número default")

        # Enviar notificación
        result = whatsapp_client.send_handoff_notification(
            user_phone=user_phone,
            reason=reason,
            to_number=vendor_whatsapp,  # Puede ser None, usará default
            user_name=user_name,
            conversation_id=conversation_id,
            additional_context=additional_context,
        )

        # Verificar resultado
        if result["status"] == "error":
            error_msg = f"Failed to send WhatsApp: {result['message']}"
            print(f"[MCP Tool] ❌ {error_msg}")
            raise Exception(error_msg)

        print(
            f"[MCP Tool] ✅ WhatsApp handoff sent successfully. SID: {result.get('message_sid')}"
        )

        return HandoffResult(
            status="success",
            message="Notificación enviada al vendedor exitosamente",
            message_sid=result.get("message_sid"),
            to_number=result.get("to"),
            from_number=result.get("from"),
            assigned_user_id=assigned_user_id,
        )
