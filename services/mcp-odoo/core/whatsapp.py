"""
Cliente de SMS usando Twilio para notificaciones de handoff.
"""

import os
from typing import Optional, Dict, Any
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from core.logger import quotation_logger


class SMSClient:
    """Cliente para enviar mensajes SMS vía Twilio"""

    def __init__(self):
        """Inicializa el cliente de Twilio con variables de entorno"""
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_WHATSAPP_FROM")  # WhatsApp format
        self.default_to_number = os.getenv("VENDEDOR_WHATSAPP")  # WhatsApp format

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
        to_number: Optional[str] = None,
        user_name: Optional[str] = None,
        conversation_id: Optional[str] = None,
        additional_context: Optional[str] = None,
        lead_data: Optional[
            Dict[str, Any]
        ] = None,  # Datos del lead/cotización si existe
        assigned_user_id: Optional[int] = None,  # Para mostrar en el mensaje
    ) -> dict:
        """
        Envía notificación de handoff al vendedor por SMS

        Args:
            user_phone: Teléfono del cliente
            reason: Motivo del handoff
            to_number: Número SMS del vendedor (opcional, usa default si no se proporciona)
            user_name: Nombre del cliente (opcional)
            conversation_id: ID de conversación en ElevenLabs (opcional)
            additional_context: Contexto adicional (opcional)
            lead_data: Datos del lead/cotización si ya se generó
            assigned_user_id: ID del vendedor asignado (para mostrar en mensaje)

        Returns:
            dict con status y message_sid o error
        """
        if not self.is_configured():
            print("❌ WhatsApp client not configured")
            return {
                "status": "error",
                "message": "WhatsApp client not configured. Check environment variables.",
            }

        # Destino: VENDEDOR_WHATSAPP (número centralizado para recibir notificaciones)
        actual_target = self.default_to_number
        # El número del vendedor asignado se incluye en el cuerpo del mensaje
        selected_vendor_number = to_number or "default"

        # Construir mensaje según si hay lead_data o no
        if lead_data:
            # Formato simplificado para cotización ya generada
            message = f"""Numero: {lead_data.get('sale_order_name', 'N/A')}
Tel: {user_phone}
Contexto: {additional_context or 'Se genero la cotizacion'}

[PRUEBA]
Numero vendedor: {selected_vendor_number}""".strip()
        else:
            # Formato para solicitud de atención sin cotización
            message = f"""Se solicita atencion humana

Cliente: {user_name or 'N/A'}
Tel: {user_phone}
Contexto: {additional_context or reason}

Vendedor asignado: ID {assigned_user_id or 'N/A'}
Numero vendedor: {selected_vendor_number}""".strip()

        try:
            # Enviar WhatsApp message
            twilio_message = self.client.messages.create(
                from_=self.from_number, to=actual_target, body=message
            )

            print(f"✅ WhatsApp handoff notification sent. SID: {twilio_message.sid}")
            print(
                f"🧪 [MODO PRUEBA] Vendedor seleccionado: ID {assigned_user_id}, Número: {selected_vendor_number}"
            )
            print(f"🧪 [MODO PRUEBA] Enviado a número de prueba: {actual_target}")

            return {
                "status": "success",
                "message_sid": twilio_message.sid,
                "to": actual_target,
                "from": self.from_number,
            }

        except TwilioRestException as e:
            print(f"❌ Twilio error sending WhatsApp: {e}")
            return {"status": "error", "message": f"Twilio error: {str(e)}"}

        except Exception as e:
            print(f"❌ Unexpected error sending WhatsApp: {e}")
            return {"status": "error", "message": f"Unexpected error: {str(e)}"}


# Instancia global del cliente
sms_client = SMSClient()
