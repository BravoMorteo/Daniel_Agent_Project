#!/usr/bin/env python3
"""
SERVIDOR MCP-ODOO HÍBRIDO
==========================
Servidor híbrido: MCP Protocol + FastAPI REST

Endpoints:
- /mcp       → MCP Protocol (SSE automático en /mcp/sse)
- /api/*     → REST API (ElevenLabs, webhooks)
- /health    → Health check
"""

import uvicorn
import uuid
from typing import Dict, Any

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from mcp.server.fastmcp import FastMCP

from core import Config, OdooClient
from core.api import (
    QuotationRequest,
    QuotationResponse,
    task_manager,
    process_quotation_background,
)
from tools import load_all


# -----------------------------
# Inicialización MCP
# -----------------------------
mcp = FastMCP(Config.MCP_NAME)
deps: Dict[str, Any] = {}
_tools_loaded = False


def init_tools_once() -> None:
    """Carga cliente Odoo y registra tools modulares una sola vez"""
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

    # Cargar todos los tools
    print("[INFO] Loading tools from tools/ directory...")
    load_all(mcp, deps)

    _tools_loaded = True
    print("[INFO] MCP tools registered successfully.")


# -----------------------------
# ASGI Wrapper para arreglar Host header
# -----------------------------
_mcp_app_internal = mcp.sse_app()


async def mcp_app_wrapper(scope, receive, send):
    """
    Wrapper ASGI que permite cualquier host y delega al MCP app real.
    Necesario para compatibilidad con App Runner, ngrok y otros proxies.

    FastMCP valida el Host header contra una lista de hosts permitidos.
    Este wrapper siempre usa 'localhost:8000' internamente para FastMCP,
    permitiendo conexiones desde cualquier dominio externo.

    También intercepta las respuestas para corregir headers de Location
    en redirects que puedan contener localhost.
    """
    # Guardar el host original
    original_host = None
    original_scheme = scope.get("scheme", "http")

    if scope["type"] == "http":
        # Reemplazar el header Host con localhost para FastMCP
        headers = list(scope.get("headers", []))
        new_headers = []
        host_found = False

        for name, value in headers:
            if name.lower() == b"host":
                # Guardar el host original
                original_host = value.decode("utf-8")
                # Usar localhost para compatibilidad con FastMCP
                new_headers.append((b"host", b"localhost:8000"))
                host_found = True
            else:
                new_headers.append((name, value))

        if not host_found:
            new_headers.append((b"host", b"localhost:8000"))

        scope["headers"] = new_headers

    # Wrapper para send que intercepta respuestas
    async def send_wrapper(message):
        if message["type"] == "http.response.start" and original_host:
            # Modificar el header Location en redirects
            headers = list(message.get("headers", []))
            new_headers = []

            for name, value in headers:
                if name.lower() == b"location":
                    # Reemplazar localhost con el host original
                    location = value.decode("utf-8")
                    if "localhost:8000" in location:
                        location = location.replace(
                            "http://localhost:8000",
                            f"{original_scheme}://{original_host}",
                        )
                        value = location.encode("utf-8")
                new_headers.append((name, value))

            message["headers"] = new_headers

        await send(message)

    await _mcp_app_internal(scope, receive, send_wrapper)


# -----------------------------
# FastAPI App
# -----------------------------
app = FastAPI(
    title="MCP-Odoo Hybrid Server",
    description="MCP Protocol + REST API",
    version="2.0.0",
)

# Inicializar tools al inicio
init_tools_once()

# Montar MCP usando el wrapper ASGI
# Esto automáticamente expone:
#   /mcp/sse → SSE stream
#   /mcp/messages → JSON-RPC endpoint
app.mount("/mcp", mcp_app_wrapper)


# -----------------------------
# REST API Endpoints
# -----------------------------


@app.get("/health")
async def health_check():
    """Health check para App Runner / Docker"""
    return {"ok": True, "mcp_loaded": _tools_loaded}


@app.post("/api/quotation/async", response_model=QuotationResponse)
async def create_quotation_async(
    request: QuotationRequest, background_tasks: BackgroundTasks
):
    """Crear cotización asíncrona"""
    task_id = f"quot_{uuid.uuid4().hex[:12]}"
    task = task_manager.create_task(task_id, request.dict())
    background_tasks.add_task(process_quotation_background, task_id, request.dict())

    return QuotationResponse(
        tracking_id=task_id,
        status="queued",
        message="Cotización en proceso. Consulte el tracking_id.",
        estimated_time="20-30 segundos",
        status_url=f"/api/quotation/status/{task_id}",
    )


@app.get("/api/quotation/status/{tracking_id}")
async def get_quotation_status(tracking_id: str):
    """Consultar estado de cotización"""
    task = task_manager.get_task(tracking_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tracking ID no encontrado")
    return JSONResponse(content=task.to_dict())


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("MCP-ODOO Server Híbrido - MCP + REST API")
    print("=" * 60)
    Config.print_config()
    print("\n📡 Endpoints disponibles:")
    print(f"   • MCP Protocol:     http://{Config.HOST}:{Config.PORT}/mcp")
    print(f"     ├─ SSE Stream:    http://{Config.HOST}:{Config.PORT}/mcp/sse")
    print(f"     └─ Messages:      http://{Config.HOST}:{Config.PORT}/mcp/messages")
    print(
        f"   • Async Quotation:  http://{Config.HOST}:{Config.PORT}/api/quotation/async"
    )
    print(
        f"   • Check Status:     http://{Config.HOST}:{Config.PORT}/api/quotation/status/{{id}}"
    )
    print(f"   • Health Check:     http://{Config.HOST}:{Config.PORT}/health")
    print(f"   • API Docs:         http://{Config.HOST}:{Config.PORT}/docs")
    print("=" * 60 + "\n")

    uvicorn.run("server:app", host=Config.HOST, port=Config.PORT, reload=False)
