"""
Cliente de WhatsApp usando Twilio para notificaciones de handoff.
"""

import os
from typing import Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from core.logger import quotation_logger


class WhatsAppClient:
    """Cliente para enviar mensajes de WhatsApp vía Twilio"""

    def __init__(self):
        """Inicializa el cliente de Twilio con variables de entorno"""
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_WHATSAPP_FROM")
        self.to_number = os.getenv("VENDEDOR_WHATSAPP")

        if not all(
            [self.account_sid, self.auth_token, self.from_number, self.to_number]
        ):
            print("⚠️  WhatsApp client not configured. Missing Twilio credentials.")
            self.client = None
        else:
            self.client = Client(self.account_sid, self.auth_token)

    def is_configured(self) -> bool:
        """Verifica si el cliente está correctamente configurado"""
        return self.client is not None

    def send_handoff_notification(
        self,
        user_phone: str,
        reason: str,
        user_name: Optional[str] = None,
        conversation_id: Optional[str] = None,
        additional_context: Optional[str] = None,
    ) -> dict:
        """
        Envía notificación de handoff al vendedor por WhatsApp

        Args:
            user_phone: Teléfono del cliente
            reason: Motivo del handoff
            user_name: Nombre del cliente (opcional)
            conversation_id: ID de conversación en ElevenLabs (opcional)
            additional_context: Contexto adicional (opcional)

        Returns:
            dict con status y message_sid o error
        """
        if not self.is_configured():
            print("❌ WhatsApp client not configured")
            return {
                "status": "error",
                "message": "WhatsApp client not configured. Check environment variables.",
            }

        # Construir mensaje
        message_lines = ["🔔 *Nuevo cliente solicita atención humana*", ""]

        if user_name:
            message_lines.append(f"👤 *Cliente:* {user_name}")

        message_lines.append(f"📱 *Teléfono:* {user_phone}")
        message_lines.append(f"📝 *Motivo:* {reason}")

        if conversation_id:
            message_lines.append(f"🆔 *Conversación:* {conversation_id}")

        if additional_context:
            message_lines.append(f"\n💬 *Contexto:*\n{additional_context}")

        message = "\n".join(message_lines)

        try:
            # Enviar mensaje
            twilio_message = self.client.messages.create(
                from_=self.from_number, to=self.to_number, body=message
            )

            print(f"✅ WhatsApp handoff notification sent. SID: {twilio_message.sid}")

            return {
                "status": "success",
                "message_sid": twilio_message.sid,
                "to": self.to_number,
                "from": self.from_number,
            }

        except TwilioRestException as e:
            print(f"❌ Twilio error sending WhatsApp: {e}")
            return {"status": "error", "message": f"Twilio error: {str(e)}"}

        except Exception as e:
            print(f"❌ Unexpected error sending WhatsApp: {e}")
            return {"status": "error", "message": f"Unexpected error: {str(e)}"}


# Instancia global del cliente
whatsapp_client = WhatsAppClient()
