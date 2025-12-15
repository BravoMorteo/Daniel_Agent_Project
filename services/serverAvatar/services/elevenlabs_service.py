"""
ElevenLabs Service
==================
Maneja la integración con ElevenLabs ConvAI.
"""

import json
import base64
import asyncio
from typing import Callable, Optional
from aiohttp import ClientSession, WSMsgType

from core.config import Config
from utils import Logger


class ElevenLabsService:
    """Servicio para interactuar con ElevenLabs ConvAI"""

    def __init__(self):
        self.api_key = Config.ELEVENLABS_API_KEY
        self.ws_url = Config.ELEVENLABS_WS_URL
        self.headers = {"xi-api-key": self.api_key}

    async def relay_conversation(
        self,
        ws_client,
        on_agent_response: Callable[[str], None],
        on_user_transcript: Callable[[str], None],
        closed_event: asyncio.Event,
    ):
        """
        Establece relay bidireccional con ElevenLabs.

        Args:
            ws_client: WebSocket del cliente
            on_agent_response: Callback cuando la IA responde
            on_user_transcript: Callback con transcripción del usuario
            closed_event: Evento para coordinar cierre
        """
        async with ClientSession() as session:
            async with session.ws_connect(
                self.ws_url, headers=self.headers
            ) as ws_elevenlabs:
                Logger.success("Conectado a ElevenLabs ConvAI")

                # Tareas paralelas: cliente->elevenlabs y elevenlabs->callbacks
                await asyncio.gather(
                    self._client_to_elevenlabs(ws_client, ws_elevenlabs, closed_event),
                    self._elevenlabs_to_callbacks(
                        ws_elevenlabs,
                        on_agent_response,
                        on_user_transcript,
                        closed_event,
                    ),
                    return_exceptions=True,
                )

                Logger.info("Relay de ElevenLabs terminado")

    async def _client_to_elevenlabs(self, ws_client, ws_elevenlabs, closed_event):
        """
        Relay: Cliente → ElevenLabs
        Envía audio PCM16 del cliente a ElevenLabs
        """
        Logger.audio("Esperando audio del cliente...")

        try:
            while not closed_event.is_set():
                try:
                    msg = await asyncio.wait_for(ws_client.receive(), timeout=1.0)

                    if msg.type == WSMsgType.BINARY:
                        # Audio PCM16 → Base64 → ElevenLabs
                        audio_b64 = base64.b64encode(msg.data).decode("utf-8")
                        await ws_elevenlabs.send_json({"user_audio_chunk": audio_b64})

                    elif msg.type == WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        if data.get("type") == "close":
                            closed_event.set()
                            break

                    elif msg.type in (WSMsgType.CLOSE, WSMsgType.CLOSED):
                        closed_event.set()
                        break

                except asyncio.TimeoutError:
                    continue

        except Exception as e:
            Logger.warning(f"Error en client_to_elevenlabs: {e}")
        finally:
            Logger.info("client_to_elevenlabs terminado")

    async def _elevenlabs_to_callbacks(
        self, ws_elevenlabs, on_agent_response, on_user_transcript, closed_event
    ):
        """
        Relay: ElevenLabs → Callbacks
        Procesa respuestas de ElevenLabs y ejecuta callbacks
        """
        Logger.event("Escuchando respuestas de ElevenLabs...")
        msg_count = 0

        try:
            while not closed_event.is_set():
                try:
                    msg = await asyncio.wait_for(ws_elevenlabs.receive(), timeout=1.0)

                    if msg.type == WSMsgType.TEXT:
                        msg_count += 1
                        data = json.loads(msg.data)
                        event_type = data.get("type")

                        # Respuesta de la IA
                        if event_type == "agent_response":
                            agent_response = self._extract_agent_response(data)

                            if agent_response:
                                Logger.ai(f"ElevenLabs dice: {agent_response[:100]}...")
                                await on_agent_response(agent_response)

                        # Transcripción del usuario
                        elif event_type == "user_transcription_event":
                            transcript = data.get("user_transcription_event", {}).get(
                                "user_transcript", ""
                            )
                            if transcript:
                                Logger.info(f"👤 Usuario dijo: {transcript}")
                                await on_user_transcript(transcript)

                        # Audio generado (no lo usamos, el avatar genera su audio)
                        elif event_type == "audio_event":
                            pass

                        # Otros eventos
                        elif event_type != "ping_event":
                            Logger.event(f"ElevenLabs: {event_type}")

                    elif msg.type in (WSMsgType.CLOSE, WSMsgType.CLOSED):
                        Logger.warning("ElevenLabs cerró conexión")
                        closed_event.set()
                        break

                except asyncio.TimeoutError:
                    continue

        except Exception as e:
            Logger.warning(f"Error en elevenlabs_to_callbacks: {e}")
            import traceback

            traceback.print_exc()
        finally:
            Logger.info(f"elevenlabs_to_callbacks terminado ({msg_count} mensajes)")

    @staticmethod
    def _extract_agent_response(data: dict) -> Optional[str]:
        """Extrae la respuesta del agente del JSON de ElevenLabs"""
        # Intentar diferentes estructuras de respuesta
        if "agent_response" in data:
            response = data.get("agent_response", "")
        elif "agent_response_event" in data:
            response = data.get("agent_response_event", {}).get("agent_response", "")
        else:
            return None

        if response and isinstance(response, str):
            return response

        return None
