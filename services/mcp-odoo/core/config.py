"""
Configuración del Servidor MCP-Odoo
====================================
Carga y valida las variables de entorno necesarias para Odoo.
"""

import os
from typing import List
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


class Config:
    """Configuración centralizada del servidor MCP-Odoo"""

    # Odoo Configuration
    ODOO_URL = os.getenv("ODOO_URL", "")
    ODOO_DB = os.getenv("ODOO_DB", "")
    ODOO_LOGIN = os.getenv("ODOO_LOGIN", "")
    ODOO_API_KEY = os.getenv("ODOO_API_KEY", "")

    # Server Configuration
    HOST = "0.0.0.0"
    PORT = int(os.getenv("PORT", "8000"))

    # MCP Configuration
    MCP_NAME = "OdooMCP"

    # Required environment variables
    REQUIRED_ENV_VARS = ["ODOO_URL", "ODOO_DB", "ODOO_LOGIN", "ODOO_API_KEY"]

    @classmethod
    def validate(cls) -> List[str]:
        """
        Valida que las variables requeridas estén configuradas.

        Returns:
            Lista de variables faltantes (vacía si todo está OK)
        """
        missing = []
        for var in cls.REQUIRED_ENV_VARS:
            if not os.getenv(var):
                missing.append(var)
        return missing

    @classmethod
    def is_valid(cls) -> bool:
        """Retorna True si la configuración es válida"""
        return len(cls.validate()) == 0

    @classmethod
    def print_config(cls):
        """Imprime la configuración actual (sin exponer claves completas)"""
        print("=" * 70)
        print("🔧 SERVIDOR MCP-ODOO")
        print("=" * 70)
        print(f"🌐 Odoo URL: {cls.ODOO_URL}")
        print(f"🗄️  Database: {cls.ODOO_DB}")
        print(f"👤 Login: {cls.ODOO_LOGIN}")
        print(
            f"🔑 API Key: {'✓ Configurada' if cls.ODOO_API_KEY else '✗ No configurada'}"
        )
        print(f"🚀 Servidor en: http://{cls.HOST}:{cls.PORT}")
        print("=" * 70)

        missing = cls.validate()
        if missing:
            print(f"⚠️  ADVERTENCIA: Variables faltantes: {', '.join(missing)}")
            print("=" * 70)
        else:
            print("✅ Configuración válida")
            print("=" * 70)
