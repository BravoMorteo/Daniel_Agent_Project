# Integración WhatsApp Handoff

## 📱 Descripción

El endpoint `/api/elevenlabs/handoff` permite notificar a un vendedor por WhatsApp cuando un cliente solicita atención humana durante una conversación con el agente de IA de ElevenLabs.

## 🔧 Configuración

### Variables de Entorno Requeridas

Agrega estas variables a tu archivo `.env`:

```bash
# Twilio Configuration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
VENDEDOR_WHATSAPP=whatsapp:+5215512345678
```

### Obtener Credenciales de Twilio

1. Crea una cuenta en [Twilio](https://www.twilio.com/)
2. Ve a la [consola de Twilio](https://console.twilio.com/)
3. Copia tu `Account SID` y `Auth Token`
4. Configura un número de WhatsApp en Twilio
5. Agrega el número de destino (vendedor) a la sandbox de WhatsApp

## 📡 Uso del Endpoint

### POST `/api/elevenlabs/handoff`

Notifica al vendedor cuando un cliente solicita atención humana.

**Request Body:**

```json
{
  "user_phone": "+5215512345678",
  "reason": "Cliente desea información sobre cotizaciones",
  "user_name": "Juan Pérez",
  "conversation_id": "conv_abc123",
  "additional_context": "El cliente preguntó por robots para restaurante"
}
```

**Campos:**
- `user_phone` (requerido): Teléfono del cliente en formato internacional
- `reason` (requerido): Motivo del handoff
- `user_name` (opcional): Nombre del cliente
- `conversation_id` (opcional): ID de la conversación en ElevenLabs
- `additional_context` (opcional): Contexto adicional de la conversación

**Response Exitosa (200):**

```json
{
  "status": "ok",
  "message": "Notificación enviada al vendedor",
  "message_sid": "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

**Response Error (500/503):**

```json
{
  "detail": "WhatsApp service not configured. Check TWILIO_* environment variables."
}
```

## 💬 Formato del Mensaje WhatsApp

El vendedor recibirá un mensaje formateado así:

```
🔔 *Nuevo cliente solicita atención humana*

👤 *Cliente:* Juan Pérez
📱 *Teléfono:* +5215512345678
📝 *Motivo:* Cliente desea información sobre cotizaciones
🆔 *Conversación:* conv_abc123

💬 *Contexto:*
El cliente preguntó por robots para restaurante
```

## 🧪 Prueba con cURL

```bash
curl -X POST http://localhost:8000/api/elevenlabs/handoff \
  -H "Content-Type: application/json" \
  -d '{
    "user_phone": "+5215512345678",
    "reason": "Cliente desea hablar con vendedor",
    "user_name": "María González",
    "conversation_id": "conv_test123"
  }'
```

## 🔗 Integración con ElevenLabs

En tu conversational AI de ElevenLabs, configura un webhook que llame a este endpoint cuando el cliente solicite hablar con un humano:

1. Ve a tu agente en ElevenLabs
2. Configura un custom tool o webhook
3. Apunta al endpoint: `https://tu-servidor.com/api/elevenlabs/handoff`
4. Envía los datos del cliente en el formato especificado

## 📊 Logs

Todos los handoffs se registran en los logs del servidor:

```
[INFO] WhatsApp handoff notification sent. SID: SMxxxxxxxx
```

En caso de error:

```
[ERROR] Twilio error sending WhatsApp: [Mensaje de error]
```

## ⚠️ Notas Importantes

1. **Sandbox de WhatsApp**: En desarrollo, usa la sandbox de Twilio. En producción, necesitas un número aprobado.
2. **Formato de teléfono**: Usa siempre formato internacional con `+` y código de país.
3. **Rate limits**: Twilio tiene límites de mensajes por segundo. Considera implementar rate limiting si esperas alto volumen.
4. **Costos**: Cada mensaje WhatsApp tiene un costo. Revisa la [tabla de precios de Twilio](https://www.twilio.com/whatsapp/pricing).

## 🔐 Seguridad

- Las credenciales de Twilio se leen desde variables de entorno
- El endpoint no requiere autenticación (considera agregar API key para producción)
- Los mensajes se envían solo al número configurado en `VENDEDOR_WHATSAPP`

## 📈 Mejoras Futuras

- [ ] Autenticación con API key
- [ ] Soporte para múltiples vendedores (routing inteligente)
- [ ] Cola de mensajes para manejar rate limits
- [ ] Dashboard para ver historial de handoffs
- [ ] Integración con CRM para crear tickets automáticamente
