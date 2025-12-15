#!/usr/bin/env python3
"""
SERVIDOR HÍBRIDO CON HEYGEN STREAMING AVATAR
=============================================
Servidor refactorizado y modular para integración de:
- HeyGen Streaming Avatar
- ElevenLabs ConvAI
- LiveKit WebRTC
"""

from aiohttp import web

from core.config import Config
from handlers import index, index_public, WebSocketHandler


def create_app():
    """Crea y configura la aplicación web"""
    # Validar configuración
    Config.validate()
    Config.print_config()

    # Crear aplicación
    app = web.Application()

    # Crear handler de WebSocket
    ws_handler = WebSocketHandler()

    # Configurar rutas
    app.router.add_get("/", index)
    app.router.add_get("/public", index_public)
    app.router.add_get("/hybrid", ws_handler.handle_streaming_conversation)

    return app


if __name__ == "__main__":
    app = create_app()
    web.run_app(app, host=Config.HOST, port=Config.PORT)
