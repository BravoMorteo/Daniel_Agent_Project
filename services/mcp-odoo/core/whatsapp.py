"""
Cliente de SMS/WhatsApp usando Twilio para notificaciones de handoff.
Soporta múltiples canales y ambientes (dev/prod) mediante variables de entorno.
"""

import os
from typing import Optional, Dict, Any
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from core.logger import quotation_logger


class SMSClient:
    """Cliente para enviar mensajes SMS/WhatsApp vía Twilio"""

    def __init__(self):
        """Inicializa el cliente de Twilio con variables de entorno"""
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")

        # Variables de configuración dinámica
        self.message_channel = os.getenv(
            "MESSAGE_CHANNEL", "whatsapp"
        ).lower()  # sms o whatsapp
        self.environment = os.getenv("ODOO_ENVIRONMENT", "dev").lower()  # dev o prod
        self.enable_error_notifications = (
            os.getenv("ENABLE_ERROR_NOTIFICATIONS", "true").lower() == "true"
        )

        # Números de origen según canal
        self.from_whatsapp = os.getenv("TWILIO_WHATSAPP_FROM")  # WhatsApp format
        self.from_sms = os.getenv("TWILIO_SMS_FROM")  # SMS format

        # Número de fallback para errores (número fijo)
        self.error_fallback_number = os.getenv(
            "VENDEDOR_WHATSAPP"
        )  # Para notificaciones de error

        if not all([self.account_sid, self.auth_token]):
            print("⚠️  Twilio client not configured. Missing credentials.")
            self.client = None
        else:
            self.client = Client(self.account_sid, self.auth_token)

        # Log de configuración
        print(f"📱 SMS/WhatsApp Client configurado:")
        print(f"   Canal: {self.message_channel}")
        print(f"   Ambiente: {self.environment}")
        print(
            f"   Notificaciones de error: {'✅ Habilitadas' if self.enable_error_notifications else '❌ Deshabilitadas'}"
        )

    def is_configured(self) -> bool:
        """Verifica si el cliente está correctamente configurado"""
        if not self.client:
            return False

        # Verificar que exista el número FROM según el canal
        if self.message_channel == "whatsapp":
            return self.from_whatsapp is not None
        else:  # sms
            return self.from_sms is not None

    def get_from_number(self) -> str:
        """Obtiene el número FROM según el canal configurado"""
        if self.message_channel == "whatsapp":
            return self.from_whatsapp
        else:
            return self.from_sms

    def format_number(self, number: str) -> str:
        """
        Formatea el número según el canal.
        WhatsApp: whatsapp:+1234567890
        SMS: +1234567890
        """
        if not number:
            return None

        # Limpiar formato existente
        clean_number = number.replace("whatsapp:", "").strip()

        # Aplicar formato según canal
        if self.message_channel == "whatsapp":
            if not clean_number.startswith("whatsapp:"):
                return f"whatsapp:{clean_number}"
            return clean_number
        else:
            return clean_number

    def send_handoff_notification(
        self,
        user_phone: str,
        reason: str,
        to_number: Optional[str] = None,
        user_name: Optional[str] = None,
        conversation_id: Optional[str] = None,
        additional_context: Optional[str] = None,
        lead_data: Optional[Dict[str, Any]] = None,
        assigned_user_id: Optional[int] = None,
        is_error_notification: bool = False,  # NUEVO: indica si es notificación de error
    ) -> dict:
        """
        Envía notificación de handoff al vendedor por SMS/WhatsApp

        Args:
            user_phone: Teléfono del cliente
            reason: Motivo del handoff
            to_number: Número del vendedor (REQUERIDO para notificaciones normales)
            user_name: Nombre del cliente (opcional)
            conversation_id: ID de conversación en ElevenLabs (opcional)
            additional_context: Contexto adicional (opcional)
            lead_data: Datos del lead/cotización si ya se generó
            assigned_user_id: ID del vendedor asignado
            is_error_notification: Si es True, usa número fijo y verifica ENABLE_ERROR_NOTIFICATIONS

        Returns:
            dict con status y message_sid o error
        """
        if not self.is_configured():
            print(f"❌ {self.message_channel.upper()} client not configured")
            return {
                "status": "error",
                "message": f"{self.message_channel.upper()} client not configured. Check environment variables.",
            }

        # 🚨 LÓGICA DE NOTIFICACIONES DE ERROR
        if is_error_notification:
            if not self.enable_error_notifications:
                print(
                    "⚠️ Notificaciones de error deshabilitadas (ENABLE_ERROR_NOTIFICATIONS=false)"
                )
                return {
                    "status": "skipped",
                    "message": "Error notifications disabled by configuration",
                }

            # Usar número de fallback para errores
            actual_target = self.format_number(self.error_fallback_number)
            if not actual_target:
                print(
                    "❌ No se configuró VENDEDOR_WHATSAPP para notificaciones de error"
                )
                return {
                    "status": "error",
                    "message": "Error fallback number not configured",
                }
        else:
            # 📱 NOTIFICACIONES NORMALES: Enviar directo al vendedor
            actual_target = self.format_number(to_number)
            if not actual_target:
                print("❌ No se proporcionó número del vendedor (to_number)")
                return {"status": "error", "message": "Vendor number not provided"}

        # Construir mensaje según si hay lead_data o no
        if lead_data:
            # Formato simplificado para cotización ya generada (SIN [PRUEBA])
            message = f"""Numero: {lead_data.get('sale_order_name', 'N/A')}
Tel: {user_phone}
Contexto: {additional_context or 'Se genero la cotizacion'}""".strip()
        else:
            # Formato para solicitud de atención sin cotización
            message = f"""Se solicita atencion humana

Cliente: {user_name or 'N/A'}
Tel: {user_phone}
Contexto: {additional_context or reason}

Vendedor asignado: ID {assigned_user_id or 'N/A'}""".strip()

        try:
            # Enviar mensaje
            from_number = self.get_from_number()
            twilio_message = self.client.messages.create(
                from_=from_number, to=actual_target, body=message
            )

            channel_emoji = "📱" if self.message_channel == "whatsapp" else "💬"
            print(
                f"{channel_emoji} {self.message_channel.upper()} notification sent. SID: {twilio_message.sid}"
            )
            print(f"   Destino: {actual_target}")
            print(f"   Ambiente: {self.environment}")

            if is_error_notification:
                print(f"   🚨 Tipo: Notificación de ERROR")

            return {
                "status": "success",
                "message_sid": twilio_message.sid,
                "to": actual_target,
                "from": from_number,
                "channel": self.message_channel,
                "environment": self.environment,
            }

        except TwilioRestException as e:
            print(f"❌ Twilio error sending {self.message_channel}: {e}")
            return {"status": "error", "message": f"Twilio error: {str(e)}"}

        except Exception as e:
            print(f"❌ Unexpected error sending {self.message_channel}: {e}")
            return {"status": "error", "message": f"Unexpected error: {str(e)}"}


# Instancia global del cliente
sms_client = SMSClient()
