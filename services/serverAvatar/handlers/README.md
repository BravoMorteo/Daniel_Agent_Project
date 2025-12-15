# Handlers

Manejadores HTTP y WebSocket para el servidor Avatar.

## 📁 Contenido

### `http_handlers.py`
Handlers para servir páginas HTML estáticas.

**Funciones:**
- `index(request)` - Sirve `index_livekit.html`
- `index_public(request)` - Sirve `index_public.html`

### `websocket_handler.py`
Handler principal para conversaciones streaming.

**Clase:** `WebSocketHandler`

**Método principal:**
- `handle_streaming_conversation(request)` - Orquesta todo el flujo

**Flujo:**
1. Crear avatar (HeyGen)
2. Enviar credenciales LiveKit al cliente
3. Esperar confirmación del cliente
4. Iniciar sesión del avatar
5. Enviar mensaje de bienvenida
6. Establecer relay con ElevenLabs
7. Procesar conversación en tiempo real

## 🔄 Arquitectura

```
Cliente WebSocket
        ↓
WebSocketHandler
        ↓
    ┌───┴───┐
    │       │
HeyGen  ElevenLabs
Service  Service
```

## 📝 Uso

Los handlers son registrados automáticamente en `server.py`:

```python
ws_handler = WebSocketHandler()
app.router.add_get("/hybrid", ws_handler.handle_streaming_conversation)
```
