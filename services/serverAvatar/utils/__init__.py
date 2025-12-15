"""
Logger Utility
==============
Sistema de logging centralizado para el servidor.
"""


class Logger:
    """Logger simple con emojis para mejor visualización"""

    @staticmethod
    def info(message: str):
        """Log de información"""
        print(f"ℹ️  {message}")

    @staticmethod
    def success(message: str):
        """Log de éxito"""
        print(f"✅ {message}")

    @staticmethod
    def warning(message: str):
        """Log de advertencia"""
        print(f"⚠️  {message}")

    @staticmethod
    def error(message: str):
        """Log de error"""
        print(f"❌ {message}")

    @staticmethod
    def debug(message: str):
        """Log de debug"""
        print(f"🔍 {message}")

    @staticmethod
    def event(message: str):
        """Log de evento"""
        print(f"📨 {message}")

    @staticmethod
    def avatar(message: str):
        """Log relacionado con avatar"""
        print(f"🎭 {message}")

    @staticmethod
    def audio(message: str):
        """Log relacionado con audio"""
        print(f"🎤 {message}")

    @staticmethod
    def video(message: str):
        """Log relacionado con video"""
        print(f"📹 {message}")

    @staticmethod
    def ai(message: str):
        """Log relacionado con IA"""
        print(f"🤖 {message}")
