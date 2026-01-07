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
    HandoffRequest,
    task_manager,
    process_quotation_background,
)
from core.whatsapp import sms_client
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


@app.post("/api/elevenlabs/handoff")
async def elevenlabs_handoff(request: HandoffRequest):
    """
    Endpoint para handoff desde ElevenLabs a SMS.

    Cuando un cliente solicita hablar con un humano en ElevenLabs,
    este endpoint envía una notificación al vendedor por SMS.

    Lógica de asignación:
    - Si hay lead_id/sale_order_id en el request: usa ese vendedor
    - Si no: usa balanceo de carga (vendedor con menos leads)

    Args:
        request: Datos del handoff (teléfono, motivo, etc.)

    Returns:
        Status de la notificación enviada
    """
    if not sms_client.is_configured():
        raise HTTPException(
            status_code=503,
            detail="SMS service not configured. Check TWILIO_* environment variables.",
        )

    # Importar helper y DevOdooCRMClient para la lógica de selección de vendedor
    from core.helpers import get_user_whatsapp_number
    from tools.crm import DevOdooCRMClient

    # Determinar el vendedor a quien enviar
    assigned_user_id = None
    vendor_sms = None

    client = DevOdooCRMClient()

    # Caso 1: Hay lead_id, obtener el vendedor del lead
    if hasattr(request, "lead_id") and request.lead_id:
        try:
            lead = client.read("crm.lead", request.lead_id, ["user_id"])
            if lead and lead.get("user_id"):
                assigned_user_id = lead["user_id"][0]
                print(
                    f"[API Handoff] ✅ Vendedor del lead {request.lead_id}: {assigned_user_id}"
                )
        except Exception as e:
            print(f"[API Handoff] ⚠️  Error obteniendo vendedor del lead: {e}")

    # Caso 2: Hay sale_order_id, obtener el vendedor de la orden
    elif hasattr(request, "sale_order_id") and request.sale_order_id:
        try:
            order = client.read("sale.order", request.sale_order_id, ["user_id"])
            if order and order.get("user_id"):
                assigned_user_id = order["user_id"][0]
                print(
                    f"[API Handoff] ✅ Vendedor de la orden {request.sale_order_id}: {assigned_user_id}"
                )
        except Exception as e:
            print(f"[API Handoff] ⚠️  Error obteniendo vendedor de la orden: {e}")

    # Caso 3: No hay lead ni orden, usar lógica de "vendedor con menos leads"
    if not assigned_user_id:
        print(f"[API Handoff] 🔍 Buscando vendedor con menos leads...")
        try:
            assigned_user_id = client.get_salesperson_with_least_opportunities()
            if assigned_user_id:
                print(f"[API Handoff] ✅ Vendedor con menos leads: {assigned_user_id}")
            else:
                print(f"[API Handoff] ⚠️  No se encontró vendedor disponible")
        except Exception as e:
            print(f"[API Handoff] ⚠️  Error obteniendo vendedor con menos leads: {e}")

    # Obtener el número SMS del vendedor
    if assigned_user_id:
        vendor_sms = get_user_whatsapp_number(client, assigned_user_id)
        # Limpiar prefijo whatsapp: si existe
        if vendor_sms and vendor_sms.startswith("whatsapp:"):
            vendor_sms = vendor_sms.replace("whatsapp:", "")
        # Validar que el número no tenga 'X' (número oculto por privacidad en dev)
        if vendor_sms and ("X" in vendor_sms or "x" in vendor_sms):
            print(
                f"[API Handoff] ⚠️  Número del vendedor oculto por privacidad, usando default"
            )
            vendor_sms = None
        if not vendor_sms:
            print(
                f"[API Handoff] ⚠️  No se pudo obtener número SMS válido del vendedor {assigned_user_id}, usando default"
            )
    else:
        print(f"[API Handoff] ⚠️  No se asignó vendedor, usando número default")

    result = sms_client.send_handoff_notification(
        user_phone=request.user_phone,
        reason=request.reason,
        to_number=vendor_sms,  # Pasar el número seleccionado
        user_name=request.user_name,
        conversation_id=request.conversation_id,
        additional_context=request.additional_context,
        assigned_user_id=assigned_user_id,  # Pasar ID del vendedor para el mensaje
    )

    if result["status"] == "error":
        # Log error handoff
        try:
            from datetime import datetime
            import uuid
            from core.logger import quotation_logger

            handoff_id = (
                f"sms_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"
            )
            quotation_logger.log_sms_handoff(
                handoff_id=handoff_id,
                user_phone=request.user_phone,
                reason=request.reason,
                user_name=request.user_name,
                conversation_id=request.conversation_id,
                additional_context=request.additional_context,
                lead_id=getattr(request, "lead_id", None),
                sale_order_id=getattr(request, "sale_order_id", None),
                assigned_user_id=assigned_user_id,
                vendor_sms=vendor_sms,
                message_sid=None,
                status="error",
                error=result.get("message"),
            )
        except Exception as log_err:
            print(f"[API Handoff] ⚠️  Error logging failed handoff: {log_err}")

        raise HTTPException(status_code=500, detail=result["message"])

    # Log successful handoff
    try:
        from datetime import datetime
        import uuid
        from core.logger import quotation_logger

        handoff_id = f"sms_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"
        log_path = quotation_logger.log_sms_handoff(
            handoff_id=handoff_id,
            user_phone=request.user_phone,
            reason=request.reason,
            user_name=request.user_name,
            conversation_id=request.conversation_id,
            additional_context=request.additional_context,
            lead_id=getattr(request, "lead_id", None),
            sale_order_id=getattr(request, "sale_order_id", None),
            assigned_user_id=assigned_user_id,
            vendor_sms=vendor_sms,
            message_sid=result.get("message_sid"),
            status="success",
        )
        print(f"[API Handoff] 📝 Handoff logged to: {log_path}")
    except Exception as log_err:
        print(f"[API Handoff] ⚠️  Error logging successful handoff: {log_err}")

    return {
        "status": "ok",
        "message": "Notificación SMS enviada al vendedor",
        "message_sid": result.get("message_sid"),
        "assigned_user_id": assigned_user_id,
        "selected_number": result.get("selected_number"),
    }


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
    print(
        f"   • WhatsApp Handoff: http://{Config.HOST}:{Config.PORT}/api/elevenlabs/handoff"
    )
    print(f"   • Health Check:     http://{Config.HOST}:{Config.PORT}/health")
    print(f"   • API Docs:         http://{Config.HOST}:{Config.PORT}/docs")
    print("=" * 60 + "\n")

    uvicorn.run("server:app", host=Config.HOST, port=Config.PORT, reload=False)
