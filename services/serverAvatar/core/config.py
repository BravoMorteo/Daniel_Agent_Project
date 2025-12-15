"""
Configuración del Servidor Avatar
==================================
Carga y valida las variables de entorno necesarias para HeyGen y ElevenLabs.
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


class Config:
    """Configuración centralizada del servidor"""

    # HeyGen Configuration
    HEYGEN_API_KEY = os.getenv("HeyGen_API_KEY")
    HEYGEN_AVATAR_ID = os.getenv("HEYGEN_AVATAR_ID") or os.getenv(
        "LIVEAVATAR_AVATAR_ID"
    )
    HEYGEN_VOICE_ID = "707365599f8545d5b6ce7a32a20e9c93"  # Spanish male voice

    # ElevenLabs Configuration
    ELEVENLABS_API_KEY = os.getenv("ELEVEN_API_KEY")
    ELEVENLABS_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID")

    # Server Configuration
    HOST = "0.0.0.0"
    PORT = 8000

    # HeyGen API Endpoints
    HEYGEN_BASE_URL = "https://api.heygen.com/v1"
    HEYGEN_STREAMING_NEW = f"{HEYGEN_BASE_URL}/streaming.new"
    HEYGEN_STREAMING_START = f"{HEYGEN_BASE_URL}/streaming.start"
    HEYGEN_STREAMING_STOP = f"{HEYGEN_BASE_URL}/streaming.stop"
    HEYGEN_STREAMING_TASK = f"{HEYGEN_BASE_URL}/streaming.task"

    # ElevenLabs API
    ELEVENLABS_WS_URL = (
        f"wss://api.elevenlabs.io/v1/convai/conversation?agent_id={ELEVENLABS_AGENT_ID}"
    )

    @classmethod
    def validate(cls):
        """Valida que las variables críticas estén configuradas"""
        missing = []

        if not cls.HEYGEN_API_KEY:
            missing.append("HeyGen_API_KEY")
        if not cls.HEYGEN_AVATAR_ID:
            missing.append("HEYGEN_AVATAR_ID")
        if not cls.ELEVENLABS_API_KEY:
            missing.append("ELEVEN_API_KEY")
        if not cls.ELEVENLABS_AGENT_ID:
            missing.append("ELEVENLABS_AGENT_ID")

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

        return True

    @classmethod
    def print_config(cls):
        """Imprime la configuración actual (sin exponer claves completas)"""
        print("=" * 70)
        print("🎯 SERVIDOR HÍBRIDO: HEYGEN STREAMING + ELEVENLABS")
        print("=" * 70)
        print(
            f"🔑 HeyGen API Key: {cls.HEYGEN_API_KEY[:20]}..."
            if cls.HEYGEN_API_KEY
            else "⚠️ No HeyGen API Key"
        )
        print(f"📹 Avatar ID: {cls.HEYGEN_AVATAR_ID}")
        print(f"🎤 Voice ID: {cls.HEYGEN_VOICE_ID}")
        print(f"🤖 ElevenLabs Agent: {cls.ELEVENLABS_AGENT_ID}")
        print(f"🚀 Servidor en: http://localhost:{cls.PORT}")
        print("=" * 70)
        print("\n💡 Funcionalidad:")
        print("   ✓ Usuario habla → Captura frontend")
        print("   ✓ Audio → ElevenLabs (IA procesa)")
        print("   ✓ ElevenLabs responde con TEXTO")
        print("   ✓ Texto → Avatar (comando 'talk')")
        print("   ✓ Avatar dice el texto con LABIOS SINCRONIZADOS")
        print("=" * 70)
        print()
