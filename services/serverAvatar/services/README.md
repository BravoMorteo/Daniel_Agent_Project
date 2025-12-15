# Services

Servicios de integración con APIs externas: HeyGen y ElevenLabs.

## 📁 Contenido

### `heygen_service.py`
Servicio para interactuar con HeyGen Streaming API.

**Clase:** `HeyGenService`

**Métodos principales:**
- `create_streaming_avatar()` - Crea nueva sesión, retorna LiveKit credentials
- `start_session(session_id)` - Inicia la sesión del avatar
- `stop_session(session_id)` - Detiene y cierra la sesión
- `send_task(session_id, text, task_type)` - Envía texto para que el avatar hable

**APIs usadas:**
- `POST /v1/streaming.new` - Crear sesión
- `POST /v1/streaming.start` - Iniciar sesión
- `POST /v1/streaming.stop` - Detener sesión
- `POST /v1/streaming.task` - Enviar comando

### `elevenlabs_service.py`
Servicio para integración con ElevenLabs ConvAI.

**Clase:** `ElevenLabsService`

**Métodos principales:**
- `relay_conversation()` - Establece relay bidireccional
- `_client_to_elevenlabs()` - Envía audio del usuario a ElevenLabs
- `_elevenlabs_to_callbacks()` - Procesa respuestas de IA
- `_extract_agent_response()` - Parsea respuesta JSON

**Protocolo:** WebSocket

**Mensajes manejados:**
- `user_audio_chunk` - Audio del usuario (enviado)
- `user_transcription_event` - Transcripción del usuario (recibido)
- `agent_response` - Respuesta de la IA (recibido)
- `audio_event` - Audio generado (ignorado, el avatar genera su audio)

## 🔄 Arquitectura

```
WebSocketHandler
        ↓
    ┌───┴───────┐
    │           │
HeyGenService   ElevenLabsService
    │                 │
    │                 ├─→ Audio Usuario → ElevenLabs
    │                 └─→ Respuesta IA → Callback
    │
    └─→ Texto → Avatar (sincroniza labios)
```

## 📝 Uso

```python
# Crear servicios
heygen = HeyGenService()
elevenlabs = ElevenLabsService()

# Crear avatar
avatar_data = await heygen.create_streaming_avatar()

# Establecer relay con callbacks
async def on_agent_response(text):
    await heygen.send_task(session_id, text)

await elevenlabs.relay_conversation(
    ws_client, 
    on_agent_response, 
    on_user_transcript, 
    closed_event
)
```

## 🔧 Configuración

Los servicios usan `config.py` para obtener:
- API keys
- Endpoints
- Configuración de avatar (voz, calidad, etc.)
