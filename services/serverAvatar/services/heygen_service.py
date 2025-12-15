"""
HeyGen Service
==============
Maneja todas las interacciones con la API de HeyGen Streaming Avatar.
"""

import json
from typing import Dict, Any, Optional
from aiohttp import ClientSession

from core.config import Config
from utils import Logger


class HeyGenService:
    """Servicio para interactuar con HeyGen Streaming API"""

    def __init__(self):
        self.api_key = Config.HEYGEN_API_KEY
        self.headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}

    async def create_streaming_avatar(self) -> Dict[str, Any]:
        """
        Crea una nueva sesión de Streaming Avatar.

        Returns:
            Dict con session_id, url (LiveKit), access_token, etc.
        """
        payload = {
            "quality": "medium",
            "avatar_name": Config.HEYGEN_AVATAR_ID,
            "voice": {"voice_id": Config.HEYGEN_VOICE_ID},
            "version": "v2",  # v2 devuelve LiveKit URL
            "video_encoding": "H264",  # H264 para máxima compatibilidad
        }

        async with ClientSession() as session:
            async with session.post(
                Config.HEYGEN_STREAMING_NEW, headers=self.headers, json=payload
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(
                        f"Error creating streaming avatar: {resp.status} - {text}"
                    )

                data = await resp.json()

                if data.get("code") != 100:
                    raise Exception(f"HeyGen API error: {data}")

                Logger.debug("Respuesta completa de HeyGen:")
                print(json.dumps(data, indent=2))

                session_id = data["data"]["session_id"]
                sdp = data["data"].get("sdp")
                ice_servers = data["data"].get("ice_servers2", [])
                url = data["data"].get("url")  # LiveKit URL
                access_token = data["data"].get("access_token")  # LiveKit token

                Logger.success("Streaming Avatar creado")
                Logger.info(f"   Session ID: {session_id}")
                Logger.info(f"   SDP: {'✓' if sdp else '✗'}")
                Logger.info(f"   LiveKit URL: {'✓' if url else '✗'}")
                Logger.info(f"   Access Token: {'✓' if access_token else '✗'}")

                return {
                    "session_id": session_id,
                    "sdp": sdp,
                    "ice_servers": ice_servers,
                    "url": url,
                    "access_token": access_token,
                }

    async def start_session(self, session_id: str) -> bool:
        """
        Inicia una sesión de avatar.
        Debe llamarse después de que WebRTC esté conectado.

        Args:
            session_id: ID de la sesión

        Returns:
            True si se inició correctamente
        """
        payload = {"session_id": session_id}

        async with ClientSession() as session:
            async with session.post(
                Config.HEYGEN_STREAMING_START, headers=self.headers, json=payload
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    Logger.warning(f"Error iniciando sesión: {text}")
                    return False

                data = await resp.json()
                Logger.success(f"Sesión iniciada: {data}")
                return True

    async def stop_session(self, session_id: str) -> bool:
        """
        Detiene y cierra una sesión de avatar.

        Args:
            session_id: ID de la sesión

        Returns:
            True si se detuvo correctamente
        """
        payload = {"session_id": session_id}

        async with ClientSession() as session:
            async with session.post(
                Config.HEYGEN_STREAMING_STOP, headers=self.headers, json=payload
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    Logger.warning(f"Error cerrando sesión: {text}")
                    return False

                data = await resp.json()
                Logger.success(f"Sesión cerrada: {data}")
                return True

    async def send_task(
        self, session_id: str, text: str, task_type: str = "repeat"
    ) -> Optional[Dict[str, Any]]:
        """
        Envía un comando al avatar para que hable.

        Args:
            session_id: ID de la sesión
            text: Texto que el avatar debe hablar
            task_type: "repeat" (repite texto) o "chat" (responde con knowledge base)

        Returns:
            Respuesta de la API o None si falla
        """
        payload = {
            "session_id": session_id,
            "text": text,
            "task_type": task_type,
            "task_mode": "sync",
        }

        Logger.debug("Enviando al avatar:")
        Logger.info(f"   Texto: '{text[:80]}...'")
        Logger.info(f"   Task type: {task_type}")
        Logger.debug(f"   Payload completo: {payload}")

        async with ClientSession() as session:
            async with session.post(
                Config.HEYGEN_STREAMING_TASK, headers=self.headers, json=payload
            ) as resp:
                response_text = await resp.text()

                if resp.status != 200:
                    Logger.error(f"Error {resp.status} al enviar comando")
                    Logger.error(f"   Respuesta: {response_text}")
                    return None

                data = json.loads(response_text)
                Logger.success("Avatar aceptó el comando")
                Logger.info(
                    f"   Duration: {data.get('data', {}).get('duration_ms', 'N/A')} ms"
                )
                Logger.info(f"   Task ID: {data.get('data', {}).get('task_id', 'N/A')}")
                return data
