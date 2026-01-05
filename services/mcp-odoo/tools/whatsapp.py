"""
MCP Tool para WhatsApp Handoff
Permite enviar notificaciones de handoff a vendedores por WhatsApp
"""

from typing import Optional
from pydantic import BaseModel

from core.whatsapp import whatsapp_client


class HandoffResult(BaseModel):
    """Modelo para el resultado del handoff"""

    status: str
    message: str
    message_sid: Optional[str] = None
    to_number: Optional[str] = None
    from_number: Optional[str] = None


def register(mcp, deps: dict):
    """
    Registra la herramienta MCP para WhatsApp Handoff.

    Esta herramienta permite enviar notificaciones al vendedor
    cuando un cliente solicita atención humana.
    """

    @mcp.tool(
        name="whatsapp_handoff",
        description="Envía notificación al vendedor por WhatsApp cuando un cliente solicita atención humana (handoff desde ElevenLabs u otro canal)",
    )
    def whatsapp_handoff(
        user_phone: str,
        reason: str,
        user_name: Optional[str] = None,
        conversation_id: Optional[str] = None,
        additional_context: Optional[str] = None,
    ) -> HandoffResult:
        """
        Envía una notificación de handoff al vendedor por WhatsApp.

        Args:
            user_phone: Teléfono del cliente en formato internacional (ej: +5215512345678)
            reason: Motivo del handoff (ej: "Cliente desea hablar con vendedor")
            user_name: Nombre del cliente (opcional)
            conversation_id: ID de la conversación en ElevenLabs (opcional)
            additional_context: Contexto adicional de la conversación (opcional)

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

        # Enviar notificación
        result = whatsapp_client.send_handoff_notification(
            user_phone=user_phone,
            reason=reason,
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
        )
