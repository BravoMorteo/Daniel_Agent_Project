"""
WebSocket Handler
=================
Maneja la conversación streaming híbrida entre cliente, HeyGen y ElevenLabs.
"""

import asyncio
from aiohttp import web

from services import HeyGenService, ElevenLabsService
from utils import Logger


class WebSocketHandler:
    """Maneja las conexiones WebSocket para conversaciones híbridas"""

    def __init__(self):
        self.heygen = HeyGenService()
        self.elevenlabs = ElevenLabsService()

    async def handle_streaming_conversation(self, request):
        """
        Handler principal para conversaciones streaming.

        Flujo:
        1. Crear avatar de HeyGen
        2. Enviar info LiveKit al cliente
        3. Esperar confirmación del cliente
        4. Iniciar sesión del avatar
        5. Enviar mensaje de bienvenida
        6. Establecer relay con ElevenLabs
        7. Procesar conversación en tiempo real
        """
        ws_client = web.WebSocketResponse()
        await ws_client.prepare(request)

        Logger.avatar("Cliente conectado")

        avatar_session = None

        try:
            # 1. Crear avatar de streaming
            Logger.video("Creando Streaming Avatar...")

            try:
                avatar_data = await self.heygen.create_streaming_avatar()
                avatar_session = avatar_data["session_id"]
                Logger.success(f"Avatar creado: {avatar_session}")
            except Exception as e:
                error_msg = f"Error al crear avatar: {str(e)}"
                Logger.error(error_msg)
                await ws_client.send_json(
                    {"type": "error", "message": error_msg, "step": "create_avatar"}
                )
                await ws_client.close()
                return ws_client

            # 2. Enviar info al cliente (LiveKit URL y Access Token)
            await ws_client.send_json(
                {
                    "type": "avatar_ready",
                    "session_id": avatar_session,
                    "url": avatar_data["url"],
                    "access_token": avatar_data["access_token"],
                }
            )
            Logger.success("Avatar enviado al cliente (LiveKit)")

            # 3. Esperar confirmación del cliente
            Logger.info("⏳ Esperando confirmación del cliente...")

            try:
                client_ready_msg = await asyncio.wait_for(
                    ws_client.receive_json(), timeout=30.0
                )
                Logger.info(f"📨 Mensaje recibido del cliente: {client_ready_msg}")
            except asyncio.TimeoutError:
                Logger.error("⏱️ Timeout esperando confirmación del cliente (30s)")
                await ws_client.close()
                return ws_client

            if client_ready_msg.get("type") == "client_ready":
                Logger.success("✅ Cliente confirmó LiveKit conectado")

                # 4. Iniciar sesión del avatar
                Logger.avatar("🎬 Iniciando sesión del avatar...")
                start_result = await self.heygen.start_session(avatar_session)
                Logger.info(f"📊 Resultado start_session: {start_result}")

                # Esperar a que el avatar se active
                Logger.info("⏳ Esperando 2s a que avatar se active...")
                await asyncio.sleep(2)

                # 5. Enviar mensaje de bienvenida
                Logger.avatar("💬 Enviando mensaje de bienvenida...")
                welcome_result = await self.heygen.send_task(
                    session_id=avatar_session,
                    text="¡Hola! Estoy listo para ayudarte.",
                    task_type="repeat",
                )

                Logger.info(f"📊 Resultado bienvenida: {welcome_result}")

                if welcome_result and welcome_result.get("code") == 100:
                    Logger.success("✅ Avatar hablando bienvenida")
                else:
                    Logger.warning(f"⚠️ Error en bienvenida: {welcome_result}")

            # 6. Conectar a ElevenLabs y establecer relay
            Logger.ai("Conectando a ElevenLabs...")
            await ws_client.send_json({"type": "elevenlabs_connected"})

            closed = asyncio.Event()

            # Callbacks para procesar respuestas de ElevenLabs
            async def on_agent_response(text: str):
                """Cuando la IA responde, enviar al avatar"""
                Logger.avatar(f"Enviando a avatar: '{text[:50]}...'")

                repeat_result = await self.heygen.send_task(
                    session_id=avatar_session, text=text, task_type="repeat"
                )

                if repeat_result and repeat_result.get("code") == 100:
                    Logger.audio("Avatar sincronizando labios...")
                else:
                    Logger.error(f"Error en repeat: {repeat_result}")

                # Enviar transcripción al cliente
                await ws_client.send_json({"type": "agent_response", "text": text})

            async def on_user_transcript(text: str):
                """Enviar transcripción del usuario al cliente"""
                await ws_client.send_json({"type": "user_transcript", "text": text})

            # 7. Procesar conversación
            await self.elevenlabs.relay_conversation(
                ws_client, on_agent_response, on_user_transcript, closed
            )

            Logger.info("Conversación terminada")

        except Exception as e:
            Logger.error(f"Error: {e}")
            import traceback

            traceback.print_exc()
            await ws_client.send_json({"type": "error", "message": str(e)})

        finally:
            # Cerrar sesión del avatar
            if avatar_session:
                Logger.avatar("Cerrando sesión del avatar...")
                await self.heygen.stop_session(avatar_session)

            Logger.avatar("Cliente desconectado")
            await ws_client.close()

        return ws_client
