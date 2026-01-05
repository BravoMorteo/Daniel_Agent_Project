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
        self.default_to_number = os.getenv("VENDEDOR_WHATSAPP")  # Fallback

        if not all([self.account_sid, self.auth_token, self.from_number]):
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
        to_number: Optional[str] = None,  # Número del vendedor a quien enviar
        user_name: Optional[str] = None,
        conversation_id: Optional[str] = None,
        additional_context: Optional[str] = None,
    ) -> dict:
        """
        Envía notificación de handoff al vendedor por WhatsApp

        Args:
            user_phone: Teléfono del cliente
            reason: Motivo del handoff
            to_number: Número de WhatsApp del vendedor (opcional, usa default si no se proporciona)
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

        # Usar el número proporcionado o el default
        target_number = to_number or self.default_to_number

        if not target_number:
            print("❌ No target WhatsApp number provided")
            return {
                "status": "error",
                "message": "No target WhatsApp number provided and no default configured.",
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

        # 🧪 MODO PRUEBA: Mostrar el número seleccionado en el mensaje
        if to_number:
            message_lines.append(f"\n🧪 *[PRUEBA] Vendedor seleccionado:* {to_number}")
            message_lines.append(f"📤 *[PRUEBA] Enviando a:* {self.default_to_number}")
        else:
            message_lines.append(
                f"\n📤 *Enviando a número default:* {self.default_to_number}"
            )

        message = "\n".join(message_lines)

        try:
            # 🧪 MODO PRUEBA: Siempre enviar al número default para pruebas
            actual_target = self.default_to_number

            # Enviar mensaje
            twilio_message = self.client.messages.create(
                from_=self.from_number, to=actual_target, body=message
            )

            print(f"✅ WhatsApp handoff notification sent. SID: {twilio_message.sid}")
            print(f"🧪 [MODO PRUEBA] Número seleccionado: {to_number or 'default'}")
            print(f"🧪 [MODO PRUEBA] Enviado a: {actual_target}")

            return {
                "status": "success",
                "message_sid": twilio_message.sid,
                "to": actual_target,  # Número real al que se envió
                "selected_number": to_number,  # Número que fue seleccionado por lógica
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
