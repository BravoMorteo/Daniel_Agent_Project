# Arquitectura ServerAvatar

## 🏗️ Visión General

ServerAvatar implementa una arquitectura modular de 3 capas para orquestar conversaciones en tiempo real con avatares IA.

## 📐 Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                       FRONTEND                              │
│  (Navegador con WebRTC + LiveKit + Micrófono)              │
└────────────────┬───────────────┬────────────────────────────┘
                 │               │
        WebSocket│               │LiveKit/WebRTC
                 │               │
┌────────────────▼───────────────▼────────────────────────────┐
│                    SERVER.PY (Main)                         │
│  - Inicialización de la app                                 │
│  - Validación de configuración                              │
│  - Registro de rutas                                        │
└────────────────┬────────────────────────────────────────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
┌───▼─────────────┐  ┌────────▼──────────┐
│  CORE/          │  │   HANDLERS/       │
│                 │  │                   │
│ ┌────────────┐  │  │ ┌───────────────┐ │
│ │ config.py  │  │  │ │ http_handlers │ │
│ │            │  │  │ └───────────────┘ │
│ │ - Env vars │  │  │ ┌───────────────┐ │
│ │ - Validar  │  │  │ │ websocket_    │ │
│ └────────────┘  │  │ │   handler     │ │
└─────────────────┘  │ └───────┬───────┘ │
                     └─────────┼─────────┘
                               │
              ┌────────────────┴────────────────┐
              │                                  │
    ┌─────────▼──────────┐         ┌───────────▼─────────┐
    │   SERVICES/        │         │     UTILS/          │
    │                    │         │                     │
    │ ┌────────────────┐ │         │ - Logger (emojis)  │
    │ │ heygen_service │ │         │ - Helpers          │
    │ └────────────────┘ │         └────────────────────┘
    │                    │
    │ ┌────────────────┐ │
    │ │elevenlabs_     │ │
    │ │  service       │ │
    │ └────────────────┘ │
    └─────────┬──────────┘
              │
    ┌─────────┴──────────────────────┐
    │                                 │
┌───▼──────────────┐    ┌────────────▼──────────┐
│  HeyGen API      │    │  ElevenLabs API       │
│  (Avatar)        │    │  (ConvAI)             │
└──────────────────┘    └───────────────────────┘
```

## 🎯 Capas de la Arquitectura

### 1. **Capa de Presentación** (`handlers/`)

**Responsabilidad:** Manejar requests HTTP y WebSocket

#### `http_handlers.py`
- Sirve páginas HTML estáticas
- Endpoints: `/`, `/public`

#### `websocket_handler.py`
- Orquesta el flujo completo de conversación
- Coordina HeyGen y ElevenLabs
- Maneja el ciclo de vida de la sesión

**Patrón:** Handler Pattern

### 2. **Capa de Servicios** (`services/`)

**Responsabilidad:** Encapsular integraciones externas

#### `heygen_service.py`
Operaciones con HeyGen API:
- `create_streaming_avatar()` - Inicializar sesión
- `start_session()` - Activar avatar
- `stop_session()` - Cerrar sesión
- `send_task()` - Enviar texto para hablar

#### `elevenlabs_service.py`
Operaciones con ElevenLabs:
- `relay_conversation()` - Establecer comunicación bidireccional
- `_client_to_elevenlabs()` - Relay de audio del usuario
- `_elevenlabs_to_callbacks()` - Procesar respuestas de IA
- `_extract_agent_response()` - Parsear respuestas JSON

**Patrón:** Service Layer Pattern, Facade Pattern

### 3. **Capa de Configuración y Utilidades** (`core/`, `utils/`)

**Responsabilidad:** Configuración y utilidades compartidas

#### `core/config.py`
- Carga variables de entorno desde `.env`
- Validación de configuración requerida
- Constantes de API endpoints
- Método `validate()` para inicialización

#### `utils/`
- `Logger`: Logging consistente con emojis
- Funciones helper compartidas

**Patrón:** Singleton Pattern (Config), Utility Pattern

## 🔄 Flujo de Ejecución

### Inicialización (server.py)

```python
1. Cargar configuración (Config)
2. Validar variables requeridas
3. Crear aplicación aiohttp
4. Registrar rutas HTTP y WebSocket
5. Iniciar servidor en puerto 8000
```

### Conversación Streaming (websocket_handler.py)

```python
1. Cliente se conecta → WebSocketHandler.handle_streaming_conversation()
2. Crear sesión avatar → HeyGenService.create_streaming_avatar()
3. Enviar info LiveKit → Cliente recibe URL y token
4. Esperar confirmación → Cliente conecta WebRTC
5. Iniciar avatar → HeyGenService.start_session()
6. Mensaje bienvenida → HeyGenService.send_task()
7. Conectar ElevenLabs → ElevenLabsService.relay_conversation()
8. Loop de conversación:
   - Audio usuario → ElevenLabs
   - Respuesta IA → HeyGen → Avatar habla
   - Transcripciones → Cliente
9. Desconexión → HeyGenService.stop_session()
```

## 🔌 Integraciones Externas

### HeyGen Streaming API (v2)

**Endpoints usados:**
- `POST /streaming.new` - Crear sesión, obtener LiveKit credentials
- `POST /streaming.start` - Activar avatar
- `POST /streaming.task` - Enviar texto para hablar
- `POST /streaming.stop` - Cerrar sesión

**Formato de video:** H264 para compatibilidad
**Protocolo:** LiveKit WebRTC

### ElevenLabs ConvAI API

**Endpoint:** WebSocket `wss://api.elevenlabs.io/v1/convai/conversation`

**Mensajes clave:**
- `user_audio_chunk` - Audio PCM16 en Base64
- `user_transcription_event` - Transcripción del usuario
- `agent_response` - Respuesta generada por IA
- `audio_event` - Audio generado (no usado, el avatar genera su audio)

## 🎨 Patrones de Diseño

### 1. **Service Layer**
Los servicios (`HeyGenService`, `ElevenLabsService`) encapsulan la lógica de integración con APIs externas.

**Ventaja:** Fácil cambiar de proveedor (ej: HeyGen → D-ID)

### 2. **Facade**
`WebSocketHandler` actúa como fachada que simplifica la coordinación entre múltiples servicios.

**Ventaja:** El cliente solo interactúa con un punto de entrada

### 3. **Callback Pattern**
`ElevenLabsService.relay_conversation()` usa callbacks para notificar eventos:
```python
on_agent_response: Callable[[str], None]
on_user_transcript: Callable[[str], None]
```

**Ventaja:** Desacoplamiento entre procesamiento y acción

### 4. **Async/Await**
Todo el servidor es asíncrono usando `asyncio` y `aiohttp`.

**Ventaja:** Manejo eficiente de I/O (red, WebSocket)

## 📦 Dependencias entre Módulos

```
```
server.py
  ↓
  ├─→ core/config.py
  ├─→ handlers/
  │     ├─→ http_handlers.py
  │     └─→ websocket_handler.py
  │           ↓
  │           ├─→ services/heygen_service.py
  │           │     ↓
  │           │     └─→ core/config.py, utils/
  │           │
  │           ├─→ services/elevenlabs_service.py
  │           │     ↓
  │           │     └─→ core/config.py, utils/
  │           │
  │           └─→ utils/
  │
  └─→ utils/
```

**Principio aplicado:** Dependencias fluyen hacia abajo (no hay dependencias circulares)

## 🧪 Testing Strategy

### Unit Tests
- `test_heygen_service.py` - Mock de aiohttp para probar creación de avatar
- `test_elevenlabs_service.py` - Mock de WebSocket para probar relay
- `test_config.py` - Validación de configuración

### Integration Tests
- `test_websocket_flow.py` - Flujo completo end-to-end
- Mock de APIs externas para no consumir créditos

### Load Tests
- Múltiples conexiones simultáneas
- Tiempo de respuesta de avatar

## 🔒 Seguridad

### Variables de Entorno
- API keys nunca hardcodeadas
- `.env` en `.gitignore`
- Validación en `Config.validate()`

### WebSocket
- Solo permitir conexiones del mismo origen en producción
- Rate limiting recomendado
- Timeout de conexiones

## 🚀 Escalabilidad

### Horizontal Scaling
- Servidor stateless (sesiones en HeyGen/ElevenLabs)
- Múltiples instancias detrás de load balancer

### Vertical Scaling
- asyncio permite miles de conexiones concurrentes
- Limitado por memoria para WebSocket buffers

### Optimizaciones
- Connection pooling en `aiohttp.ClientSession`
- Reuso de sesiones de avatar si es posible

## 📈 Métricas Importantes

- **Latencia avatar:** Tiempo desde texto → labios sincronizados
- **Latencia IA:** Tiempo de respuesta de ElevenLabs
- **Conexiones activas:** Número de WebSockets abiertos
- **Tasa de error:** Fallos en APIs externas

## 🔧 Extensibilidad

### Agregar nuevo proveedor de avatar
1. Crear `services/nuevo_avatar_service.py`
2. Implementar misma interfaz que `HeyGenService`
3. Modificar `websocket_handler.py` para usar nuevo servicio

### Agregar nueva funcionalidad
1. Crear nuevo handler en `handlers/`
2. Registrar ruta en `server.py`
3. Usar servicios existentes o crear nuevos

---

**Principios de diseño:**
- ✅ Separación de responsabilidades
- ✅ Bajo acoplamiento
- ✅ Alta cohesión
- ✅ Código testeable
- ✅ Fácil de extender

**Última actualización:** 15 de diciembre de 2025
