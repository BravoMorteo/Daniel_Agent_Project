#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════
SERVIDOR HÍBRIDO: HEYGEN STREAMING AVATAR + ELEVENLABS CONVAI
═══════════════════════════════════════════════════════════════════════

DESCRIPCIÓN:
    Servidor que orquesta la experiencia completa de avatar conversacional:
    - Recibe conexiones WebSocket del frontend
    - Crea sesión de streaming con HeyGen (avatar animado)
    - Conecta con ElevenLabs ConvAI (conversación IA)
    - Coordina la sincronización de audio y video en tiempo real

ARQUITECTURA:
    ┌────────────────────────────────────────────────────────┐
    │              Cliente (Navegador Web)                   │
    │  • Captura audio del micrófono                         │
    │  • Muestra video del avatar                            │
    └─────────────────┬──────────────────────────────────────┘
                      │ WebSocket
                      ▼
    ┌────────────────────────────────────────────────────────┐
    │         ServerAvatar (Este Servidor)                   │
    │  • Orquesta la conversación                            │
    │  • Relay de audio bidireccional                        │
    │  • Coordina HeyGen + ElevenLabs                        │
    └────────┬────────────────────┬──────────────────────────┘
             │                    │
             ▼                    ▼
    ┌─────────────────┐  ┌──────────────────────┐
    │  HeyGen API     │  │  ElevenLabs ConvAI   │
    │  • Video avatar │  │  • Procesa voz       │
    │  • LiveKit      │  │  • Genera respuestas │
    └─────────────────┘  └──────────────────────┘

FLUJO DE DATOS:
    1. Cliente conecta via WebSocket
    2. Servidor inicia sesión HeyGen (obtiene token LiveKit)
    3. Servidor conecta con ElevenLabs ConvAI
    4. Servidor envía info de sesión al cliente
    5. Cliente conecta a LiveKit y comienza streaming
    6. Audio del usuario → Servidor → ElevenLabs → Respuesta IA
    7. Video del avatar ← HeyGen ← LiveKit ← Cliente

ENDPOINTS:
    - GET  /          → Página de inicio (con avatar)
    - GET  /public    → Página pública (sin avatar)
    - WS   /hybrid    → WebSocket para conversación híbrida

USO:
    python server.py
    # Servidor en http://localhost:8080

CONFIGURACIÓN REQUERIDA (.env):
    HEYGEN_API_KEY=tu_heygen_api_key
    HEYGEN_AVATAR_ID=tu_avatar_id
    ELEVENLABS_API_KEY=tu_elevenlabs_api_key
    ELEVENLABS_AGENT_ID=tu_agent_id
    PORT=8080
    HOST=0.0.0.0

AUTOR: BravoMorteo
FECHA: Enero 2026
═══════════════════════════════════════════════════════════════════════
"""

from aiohttp import web

from core.config import Config
from handlers import index, index_public, WebSocketHandler


def create_app():
    """
    Crea y configura la aplicación web aiohttp.

    PROCESO:
        1. Valida que todas las variables de entorno estén configuradas
        2. Imprime la configuración para verificación
        3. Crea la aplicación aiohttp
        4. Crea el manejador de WebSocket
        5. Registra todas las rutas HTTP y WebSocket

    Returns:
        web.Application: Aplicación aiohttp configurada y lista para ejecutar

    RUTAS REGISTRADAS:
        - GET  /          → Página principal con avatar (index.html)
        - GET  /public    → Página pública alternativa
        - WS   /hybrid    → WebSocket para streaming conversacional

    Raises:
        ValueError: Si falta alguna variable de entorno requerida
    """
    # Validar que todas las credenciales estén configuradas
    Config.validate()

    # Mostrar configuración actual (sin mostrar secrets completos)
    Config.print_config()

    # Crear aplicación aiohttp
    app = web.Application()

    # Crear manejador de WebSocket (orquesta todo el flujo)
    ws_handler = WebSocketHandler()

    # ═══════════════════════════════════════════════════════════════
    # REGISTRO DE RUTAS
    # ═══════════════════════════════════════════════════════════════

    # Ruta principal: página con avatar
    app.router.add_get("/", index)

    # Ruta pública: página alternativa
    app.router.add_get("/public", index_public)

    # Ruta de WebSocket: conversación en tiempo real
    app.router.add_get("/hybrid", ws_handler.handle_streaming_conversation)

    return app


# ═══════════════════════════════════════════════════════════════════════
# MAIN - PUNTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    """
    Punto de entrada del servidor.

    Crea la aplicación y la ejecuta con aiohttp.

    CONFIGURACIÓN:
        - Host: Definido en Config.HOST (default: 0.0.0.0)
        - Puerto: Definido en Config.PORT (default: 8080)

    ACCESO:
        - Local: http://localhost:8080
        - Red local: http://<tu-ip>:8080
        - Producción: Configurar proxy reverso (nginx, etc.)
    """
    app = create_app()
    web.run_app(app, host=Config.HOST, port=Config.PORT)
