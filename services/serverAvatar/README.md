# ServerAvatar

Servidor híbrido para integración de HeyGen Streaming Avatar con ElevenLabs ConvAI.

## 🎯 Funcionalidad

Este servidor permite crear conversaciones en tiempo real con un avatar IA que:
1. **Escucha** al usuario a través del micrófono
2. **Procesa** el audio con ElevenLabs ConvAI (IA conversacional)
3. **Responde** con texto generado por la IA
4. **Anima** el avatar de HeyGen sincronizando labios con el texto
5. **Transmite** video en tiempo real usando LiveKit/WebRTC

## 📁 Estructura del Proyecto

```
serverAvatar/
├── server.py                   # 🚀 Punto de entrada principal
├── core/                       # 🔧 Módulos principales
│   ├── __init__.py
│   ├── config.py              # ⚙️ Configuración y variables de entorno
│   └── README.md              # Documentación del core
├── handlers/
│   ├── __init__.py
│   ├── http_handlers.py       # 📄 Handlers para páginas HTML
│   ├── websocket_handler.py   # 🌐 Handler principal de WebSocket
│   └── README.md              # Documentación de handlers
├── services/
│   ├── __init__.py
│   ├── heygen_service.py      # 🎭 Integración con HeyGen API
│   ├── elevenlabs_service.py  # 🤖 Integración con ElevenLabs
│   └── README.md              # Documentación de servicios
├── utils/
│   ├── __init__.py            # 📝 Logger y utilidades
│   └── README.md              # Documentación de utilidades
├── static_hybrid/             # 🌐 Archivos HTML del frontend
├── README.md                  # 📖 Este archivo
└── ARCHITECTURE.md            # 🏗️ Arquitectura detallada
```

## 🚀 Inicio Rápido

### 1. Configurar Variables de Entorno

Crea un archivo `.env` con:

```bash
# HeyGen
HeyGen_API_KEY=tu_api_key_de_heygen
HEYGEN_AVATAR_ID=tu_avatar_id

# ElevenLabs
ELEVEN_API_KEY=tu_api_key_de_elevenlabs
ELEVENLABS_AGENT_ID=tu_agent_id
```

### 2. Instalar Dependencias

```bash
# Con pip
pip install aiohttp python-dotenv

# O con uv (recomendado)
uv pip install aiohttp python-dotenv
```

### 3. Ejecutar Servidor

```bash
python server.py
```

El servidor estará disponible en: `http://localhost:8000`

## 🔧 Componentes

### `core/config.py`
Maneja toda la configuración del servidor:
- Carga variables de entorno desde `.env`
- Valida configuración requerida
- Expone constantes de configuración

### `handlers/websocket_handler.py`
Handler principal que orquesta:
- Creación de sesión de avatar
- Conexión con LiveKit
- Relay bidireccional con ElevenLabs
- Sincronización de labios del avatar

### `services/heygen_service.py`
Encapsula todas las llamadas a HeyGen API:
- `create_streaming_avatar()` - Crear sesión
- `start_session()` - Iniciar avatar
- `stop_session()` - Detener avatar
- `send_task()` - Enviar texto para hablar

### `services/elevenlabs_service.py`
Maneja integración con ElevenLabs:
- `relay_conversation()` - Relay bidireccional
- Procesamiento de audio del usuario
- Extracción de respuestas de la IA
- Transcripciones en tiempo real

### `utils/`
Utilidades compartidas:
- `Logger` - Sistema de logging con emojis

## 🔄 Flujo de Datos

```
Usuario habla → Micrófono
                    ↓
              [Frontend]
                    ↓
            Audio PCM16 (WebSocket)
                    ↓
         [WebSocketHandler]
                    ↓
          [ElevenLabsService]
                    ↓
         ElevenLabs ConvAI API
                    ↓
              Texto de IA
                    ↓
          [HeyGenService]
                    ↓
         HeyGen Streaming API
                    ↓
      Avatar sincroniza labios
                    ↓
          LiveKit/WebRTC
                    ↓
              [Frontend]
                    ↓
           Usuario ve avatar
```

## 📝 API Endpoints

### HTTP
- `GET /` - Página principal (index_livekit.html)
- `GET /public` - Página pública (index_public.html)

### WebSocket
- `GET /hybrid` - Conversación streaming híbrida

#### Mensajes WebSocket

**Cliente → Servidor:**
```json
{
  "type": "client_ready"  // Cliente listo para comenzar
}
```

**Servidor → Cliente:**
```json
{
  "type": "avatar_ready",
  "session_id": "...",
  "url": "wss://...",        // LiveKit URL
  "access_token": "..."      // LiveKit token
}

{
  "type": "elevenlabs_connected"
}

{
  "type": "user_transcript",
  "text": "..."              // Lo que dijo el usuario
}

{
  "type": "agent_response",
  "text": "..."              // Respuesta de la IA
}

{
  "type": "error",
  "message": "..."
}
```

## 🐛 Debug

Para ver logs detallados, el servidor usa emojis:
- 🎭 Avatar
- 🤖 IA
- 🎤 Audio
- 📹 Video
- ✅ Éxito
- ⚠️ Advertencia
- ❌ Error

## 🔐 Seguridad

- Nunca commitear el archivo `.env`
- Las API keys deben mantenerse secretas
- El servidor debe ejecutarse detrás de HTTPS en producción

## 📦 Dependencias

- `aiohttp` - Servidor web asíncrono y cliente HTTP
- `python-dotenv` - Carga variables de entorno

## 🎨 Frontend

El frontend se encuentra en `static_hybrid/`:
- `index_livekit.html` - Interfaz principal con LiveKit
- `index_public.html` - Interfaz pública

Ver `frontend/README.md` para más detalles del cliente.

## 🤝 Integración

Para usar este servidor en tu aplicación:

1. Conecta al WebSocket: `ws://localhost:8000/hybrid`
2. Espera mensaje `avatar_ready`
3. Conecta LiveKit usando `url` y `access_token`
4. Envía mensaje `{"type": "client_ready"}`
5. Comienza a enviar audio PCM16
6. Recibe transcripciones y respuestas

## 📚 Documentación

- Ver `ARCHITECTURE.md` para detalles de arquitectura
- Ver ejemplos de uso en `static_hybrid/`

## 📚 Recursos

- [HeyGen Streaming API Docs](https://docs.heygen.com/reference/streaming-api)
- [ElevenLabs ConvAI Docs](https://elevenlabs.io/docs/conversational-ai)
- [LiveKit Docs](https://docs.livekit.io/)

---

**Última actualización:** 15 de diciembre de 2025
