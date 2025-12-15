#!/usr/bin/env python3
"""
SERVIDOR MCP-ODOO
=================
Servidor Model Context Protocol para integración con Odoo ERP.
Versión refactorizada y modular.
"""

import os
import json
from typing import Dict, Any

from mcp.server.fastmcp import FastMCP

from core import Config, OdooClient
from tools import load_all


# -----------------------------
# Inicialización
# -----------------------------
mcp = FastMCP(Config.MCP_NAME)
deps: Dict[str, Any] = {}
_tools_loaded = False


def init_tools_once() -> None:
    """
    Carga cliente Odoo y registra tools modulares una sola vez (idempotente).
    """
    global _tools_loaded

    if _tools_loaded:
        return

    # Validar configuración
    missing = Config.validate()
    if missing:
        print(f"[WARN] Missing environment variables: {', '.join(missing)}")
        print("[INFO] Server will start but Odoo operations will fail.")

    # Inicializar cliente Odoo
    deps["odoo"] = OdooClient()

    # Cargar todos los tools desde el directorio tools/
    print("[INFO] Loading tools from tools/ directory...")
    load_all(mcp, deps)

    _tools_loaded = True
    print("[INFO] MCP tools registered successfully.")


# -----------------------------
# ASGI Application
# -----------------------------
_mcp_app_internal = mcp.streamable_http_app()


async def mcp_app(scope, receive, send):
    """
    Wrapper ASGI que permite cualquier host y delega al MCP app real.
    Necesario para compatibilidad con ngrok y otros proxies.
    """
    if scope["type"] == "http":
        # Guardar headers originales
        original_headers = scope.get("headers", [])

        # Filtrar y reemplazar el header Host
        new_headers = []
        host_found = False

        for name, value in original_headers:
            if name.lower() == b"host":
                # Reemplazar con localhost para pasar la validación
                new_headers.append((b"host", b"localhost:8000"))
                host_found = True
            else:
                new_headers.append((name, value))

        if not host_found:
            new_headers.append((b"host", b"localhost:8000"))

        scope["headers"] = new_headers

    # Delegar al app MCP real
    await _mcp_app_internal(scope, receive, send)


async def app(scope, receive, send):
    """
    Aplicación ASGI principal.
    Maneja /health y delega todo lo demás al servidor MCP.
    """
    # Health check endpoint para App Runner / Docker
    if scope["type"] == "http" and scope.get("path") == "/health":
        body = b'{"ok": true}'
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"content-type", b"application/json")],
            }
        )
        await send({"type": "http.response.body", "body": body})
        return

    # Primer request real: registrar tools modulares
    if not _tools_loaded:
        try:
            init_tools_once()
        except Exception as e:
            if scope["type"] == "http":
                msg = json.dumps(
                    {"error": f"init_tools_once failed: {repr(e)}"}
                ).encode("utf-8")
                await send(
                    {
                        "type": "http.response.start",
                        "status": 500,
                        "headers": [(b"content-type", b"application/json")],
                    }
                )
                await send({"type": "http.response.body", "body": msg})
                return
            raise

    # Todo lo demás lo maneja el servidor MCP (Streamable HTTP)
    await mcp_app(scope, receive, send)


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    import uvicorn

    Config.print_config()
    uvicorn.run("server:app", host=Config.HOST, port=Config.PORT)
