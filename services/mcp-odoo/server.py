#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════
SERVIDOR MCP-ODOO HÍBRIDO
═══════════════════════════════════════════════════════════════════════

DESCRIPCIÓN:
    Servidor híbrido que combina dos protocolos en un solo proceso:
    - Model Context Protocol (MCP): Para que LLMs como Claude puedan
      usar herramientas de Odoo
    - FastAPI REST: Para endpoints HTTP tradicionales (webhooks, APIs)

ARQUITECTURA:
    ┌─────────────────────────────────────────────────────┐
    │           FastAPI App (Puerto 8000)                 │
    ├─────────────────────────────────────────────────────┤
    │  /mcp/*      → MCP Protocol (SSE en /mcp/sse)      │
    │  /api/*      → REST API Endpoints                   │
    │  /health     → Health check                         │
    │  /docs       → Swagger UI automático                │
    └─────────────────────────────────────────────────────┘

ENDPOINTS PRINCIPALES:
    - /mcp/sse      → Stream SSE para Model Context Protocol
    - /api/quotation/async → Crear cotización asíncrona
    - /api/quotation/status/{id} → Consultar estado de cotización
    - /api/elevenlabs/handoff → Notificar handoff a vendedor

HERRAMIENTAS MCP DISPONIBLES:
    Las herramientas se cargan dinámicamente desde /tools:
    - CRM: create/read leads, opportunities
    - Sales: create/read/update sale orders
    - Projects: list/search projects
    - Tasks: list/search tasks
    - Users: list/search users
    - Search: búsqueda general en Odoo
    - WhatsApp: notificaciones de handoff

USO:
    python server.py
    # Servidor en http://localhost:8000
    # Docs en http://localhost:8000/docs

AUTOR: BravoMorteo
FECHA: Enero 2026
═══════════════════════════════════════════════════════════════════════
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


# ═══════════════════════════════════════════════════════════════════════
# INICIALIZACIÓN MCP
# ═══════════════════════════════════════════════════════════════════════
# El servidor MCP permite que LLMs (como Claude) usen herramientas de Odoo
# Las herramientas se registran una sola vez al inicio

mcp = FastMCP(Config.MCP_NAME)
deps: Dict[str, Any] = {}  # Dependencias compartidas (OdooClient, etc.)
_tools_loaded = False  # Flag para cargar tools solo una vez


def init_tools_once() -> None:
    """
    Inicializa el cliente Odoo y carga todas las herramientas MCP.

    Este método se ejecuta UNA SOLA VEZ al inicio del servidor.

    Proceso:
        1. Valida las variables de entorno requeridas
        2. Crea el cliente de Odoo (OdooClient)
        3. Carga dinámicamente todas las herramientas desde /tools
        4. Registra las herramientas en el servidor MCP

    Las herramientas disponibles incluyen:
        - crm.py: Gestión de leads y oportunidades
        - sales.py: Gestión de órdenes de venta
        - projects.py: Búsqueda de proyectos
        - tasks.py: Búsqueda de tareas
        - users.py: Búsqueda de usuarios
        - search.py: Búsqueda general
        - whatsapp.py: Notificaciones
    """
    global _tools_loaded

    if _tools_loaded:
        return

    # Validar configuración requerida
    missing = Config.validate()
    if missing:
        print(f"[WARN] Missing environment variables: {', '.join(missing)}")
        print("[INFO] Server will start but Odoo operations will fail.")

    # Inicializar cliente Odoo (conexión XML-RPC)
    deps["odoo"] = OdooClient()

    # Cargar todas las herramientas desde el directorio /tools
    print("[INFO] Loading tools from tools/ directory...")
    load_all(mcp, deps)

    _tools_loaded = True
    print("[INFO] MCP tools registered successfully.")


# ═══════════════════════════════════════════════════════════════════════
# ASGI WRAPPER PARA COMPATIBILIDAD CON PROXIES
# ═══════════════════════════════════════════════════════════════════════
# FastMCP valida el header "Host" contra una lista de hosts permitidos.
# Este wrapper permite conexiones desde cualquier dominio (ngrok, AWS, etc.)
# reescribiendo el Host header internamente a localhost.

_mcp_app_internal = mcp.sse_app()


async def mcp_app_wrapper(scope, receive, send):
    """
    Wrapper ASGI que permite conexiones desde cualquier host.

    PROBLEMA:
        FastMCP solo acepta conexiones desde hosts específicos.
        Esto falla cuando usas proxies como ngrok, App Runner, etc.

    SOLUCIÓN:
        Intercepta el header "Host" y lo reescribe a "localhost:8000"
        internamente para FastMCP, mientras mantiene el host original
        para respuestas.

    También corrige los headers de "Location" en redirects HTTP para
    que apunten al dominio real en lugar de localhost.

    Args:
        scope: Información de la conexión ASGI
        receive: Canal para recibir mensajes
        send: Canal para enviar respuestas
    """
    # Guardar el host original del request
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

    # Wrapper para send() que intercepta respuestas
    async def send_wrapper(message):
        """Corrige headers de Location en redirects"""
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

    # Delegar al servidor MCP real
    await _mcp_app_internal(scope, receive, send_wrapper)


# ═══════════════════════════════════════════════════════════════════════
# FASTAPI APP (REST API)
# ═══════════════════════════════════════════════════════════════════════
# Esta es la aplicación principal que expone tanto MCP como REST endpoints

app = FastAPI(
    title="MCP-Odoo Hybrid Server",
    description="Model Context Protocol + REST API para Odoo ERP",
    version="2.0.0",
)

# Inicializar herramientas MCP al inicio
init_tools_once()

# Montar el servidor MCP en /mcp
# Esto expone automáticamente:
#   /mcp/sse → Stream SSE para el protocolo MCP
#   /mcp/messages → Endpoint JSON-RPC
app.mount("/mcp", mcp_app_wrapper)


# ═══════════════════════════════════════════════════════════════════════
# REST API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════
# Endpoints HTTP tradicionales para integraciones externas


@app.get("/health")
async def health_check():
    """
    Health check para monitoreo y balanceadores de carga.

    Returns:
        dict: Estado del servidor
            - ok (bool): Siempre True si el servidor responde
            - mcp_loaded (bool): Si las herramientas MCP están cargadas

    Ejemplo:
        GET /health
        → {"ok": true, "mcp_loaded": true}
    """
    return {"ok": True, "mcp_loaded": _tools_loaded}


@app.post("/api/quotation/async", response_model=QuotationResponse)
async def create_quotation_async(
    request: QuotationRequest, background_tasks: BackgroundTasks
):
    """
    Crea una cotización completa de forma ASÍNCRONA.

    FLUJO:
        1. Valida los datos del request
        2. Genera un tracking_id único
        3. Crea una tarea en TaskManager (estado: queued)
        4. Programa procesamiento en background
        5. Retorna tracking_id inmediatamente

    El procesamiento en background:
        - Crea/busca el cliente (partner)
        - Crea el lead
        - Crea la oportunidad
        - Crea la orden de venta
        - Agrega las líneas de productos
        - Registra todo en logs (local + S3)

    Args:
        request (QuotationRequest): Datos de la cotización
            - partner_name: Nombre del cliente
            - contact_name: Nombre del contacto
            - email: Email del contacto
            - phone: Teléfono del contacto
            - lead_name: Nombre del lead/oportunidad
            - product_id: ID del producto en Odoo (opcional)
            - products: Lista de productos (alternativa)
            - product_qty: Cantidad (default: 1)
            - product_price: Precio (default: -1 = precio de Odoo)
        background_tasks: Gestor de tareas asíncronas de FastAPI

    Returns:
        QuotationResponse: Información del tracking
            - tracking_id: ID para consultar el estado
            - status: "queued" (en cola)
            - message: Mensaje informativo
            - estimated_time: Tiempo estimado de procesamiento
            - status_url: URL para consultar el estado

    Ejemplo:
        POST /api/quotation/async
        {
            "partner_name": "Acme Corp",
            "contact_name": "John Doe",
            "email": "john@acme.com",
            "phone": "+1234567890",
            "lead_name": "Cotización Robot PUDU",
            "product_id": 12345,
            "product_qty": 2
        }

        → {
            "tracking_id": "quot_abc123def456",
            "status": "queued",
            "message": "Cotización en proceso...",
            "estimated_time": "20-30 segundos",
            "status_url": "/api/quotation/status/quot_abc123def456"
        }
    """
    # Generar tracking ID único
    task_id = f"quot_{uuid.uuid4().hex[:12]}"

    # Crear tarea en TaskManager
    task = task_manager.create_task(task_id, request.dict())

    # Programar procesamiento en background
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
    """
    Consulta el estado de una cotización asíncrona.

    Estados posibles:
        - queued: En cola, esperando procesamiento
        - processing: En proceso
        - completed: Completada exitosamente
        - failed: Falló con error

    Args:
        tracking_id (str): El tracking_id devuelto por /api/quotation/async

    Returns:
        dict: Estado completo de la tarea
            - tracking_id: ID de la tarea
            - status: Estado actual
            - input: Datos del request original
            - output: Resultado (si completó)
            - error: Mensaje de error (si falló)
            - created_at: Timestamp de creación
            - updated_at: Timestamp de última actualización

    Raises:
        HTTPException 404: Si el tracking_id no existe

    Ejemplo:
        GET /api/quotation/status/quot_abc123def456

        → {
            "tracking_id": "quot_abc123def456",
            "status": "completed",
            "input": {...},
            "output": {
                "partner_id": 12345,
                "lead_id": 67890,
                "sale_order_id": 11111,
                "sale_order_name": "S12345"
            },
            "error": null,
            "created_at": "2026-01-30T10:00:00",
            "updated_at": "2026-01-30T10:00:25"
        }
    """
    task = task_manager.get_task(tracking_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tracking ID no encontrado")
    return JSONResponse(content=task.to_dict())


@app.post("/api/elevenlabs/handoff")
async def elevenlabs_handoff(request: HandoffRequest):
    """
    Endpoint para handoff: transferir cliente a un vendedor humano.

    CASOS DE USO:
        - Cliente solicita hablar con un humano en ElevenLabs
        - Sistema necesita escalar a atención personalizada
        - Cliente tiene dudas que requieren vendedor experto

    LÓGICA DE ASIGNACIÓN DE VENDEDOR:
        1. Si hay lead_id: usa el vendedor asignado al lead
        2. Si hay sale_order_id: usa el vendedor de la orden
        3. Si no hay ninguno: asigna al vendedor con menos leads (balanceo)

    PROCESO:
        1. Valida que el servicio de SMS esté configurado
        2. Determina el vendedor usando la lógica anterior
        3. Obtiene el número de WhatsApp del vendedor desde Odoo
        4. Envía notificación SMS/WhatsApp con datos del cliente
        5. Registra el handoff en logs (local + S3)

    Args:
        request (HandoffRequest): Datos del handoff
            - user_phone (str): Teléfono del cliente
            - reason (str): Motivo del handoff
            - user_name (str, opcional): Nombre del cliente
            - conversation_id (str, opcional): ID de conversación ElevenLabs
            - lead_id (int, opcional): ID del lead en Odoo
            - sale_order_id (int, opcional): ID de la orden de venta
            - additional_context (str, opcional): Contexto adicional

    Returns:
        dict: Resultado del handoff
            - status: "ok" si se envió correctamente
            - message: Mensaje de confirmación
            - message_sid: ID del mensaje de Twilio
            - assigned_user_id: ID del vendedor asignado
            - selected_number: Número al que se envió el SMS

    Raises:
        HTTPException 503: Si el servicio de SMS no está configurado
        HTTPException 500: Si falla el envío del mensaje

    Ejemplo:
        POST /api/elevenlabs/handoff
        {
            "user_phone": "+5215512345678",
            "reason": "Cliente solicita información personalizada",
            "user_name": "Juan Pérez",
            "conversation_id": "conv_abc123",
            "additional_context": "Preguntó por robots para restaurante"
        }

        → {
            "status": "ok",
            "message": "Notificación SMS enviada al vendedor",
            "message_sid": "SM1234567890",
            "assigned_user_id": 42,
            "selected_number": "+5215587654321"
        }
    """
    # Validar que el servicio de SMS esté configurado
    if not sms_client.is_configured():
        raise HTTPException(
            status_code=503,
            detail="SMS service not configured. Check TWILIO_* environment variables.",
        )

    # Importar dependencias necesarias
    from core.helpers import get_user_whatsapp_number
    from tools.crm import DevOdooCRMClient

    # Variables para el vendedor asignado
    assigned_user_id = None
    vendor_sms = None

    client = DevOdooCRMClient()

    # CASO 1: Hay lead_id, obtener el vendedor del lead
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

    # CASO 2: Hay sale_order_id, obtener el vendedor de la orden
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

    # CASO 3: No hay lead ni orden, usar balanceo de carga
    # (vendedor con menos leads activos)
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

    # Obtener el número de WhatsApp del vendedor desde Odoo
    if assigned_user_id:
        vendor_sms = get_user_whatsapp_number(client, assigned_user_id)
        # Limpiar prefijo "whatsapp:" si existe
        if vendor_sms and vendor_sms.startswith("whatsapp:"):
            vendor_sms = vendor_sms.replace("whatsapp:", "")
        # Validar que el número no esté oculto por privacidad
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

    # Enviar notificación SMS/WhatsApp
    result = sms_client.send_handoff_notification(
        user_phone=request.user_phone,
        reason=request.reason,
        to_number=vendor_sms,  # Número del vendedor o default
        user_name=request.user_name,
        conversation_id=request.conversation_id,
        additional_context=request.additional_context,
        assigned_user_id=assigned_user_id,
    )

    # Si hubo error, registrar en logs y lanzar excepción
    if result["status"] == "error":
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

    # Registrar handoff exitoso en logs
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


# ═══════════════════════════════════════════════════════════════════════
# MAIN - PUNTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    """
    Punto de entrada del servidor.

    Imprime información útil y lanza el servidor con uvicorn.

    CONFIGURACIÓN:
        - Host: Definido en Config.HOST (default: 0.0.0.0)
        - Puerto: Definido en Config.PORT (default: 8000)
        - Reload: Desactivado para producción

    ENDPOINTS DISPONIBLES:
        - MCP Protocol: http://localhost:8000/mcp
        - SSE Stream: http://localhost:8000/mcp/sse
        - API Docs: http://localhost:8000/docs
        - Health: http://localhost:8000/health
    """
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
