"""
API REST con FastAPI para operaciones asíncronas.
Endpoints para crear cotizaciones en background y consultar su estado.
"""

import uuid
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List

from core.tasks import task_manager, QuotationTask
from core.logger import quotation_logger
from core.helpers import retry_on_network_error
from tools.crm import DevOdooCRMClient


# Modelos Pydantic para validación
class ProductLine(BaseModel):
    """Modelo para una línea de producto"""

    product_id: int = Field(..., gt=0, description="ID del producto en Odoo")
    qty: float = Field(1.0, gt=0, description="Cantidad del producto")
    price: float = Field(-1.0, description="Precio unitario (-1 = usar pricelist)")

    class Config:
        json_schema_extra = {
            "example": {"product_id": 26174, "qty": 2.0, "price": -1.0}
        }


class QuotationRequest(BaseModel):
    """Modelo para solicitud de cotización con soporte para múltiples productos"""

    partner_name: str = Field(..., description="Nombre de la empresa/cliente")
    contact_name: str = Field(..., description="Nombre del contacto")
    email: str = Field(..., description="Email del contacto")
    phone: str = Field(..., description="Teléfono del contacto")
    lead_name: str = Field(..., description="Nombre/descripción del lead")

    # NUEVO: Array de productos (para múltiples productos diferentes)
    products: Optional[List[ProductLine]] = Field(
        None, description="Lista de productos a agregar (formato nuevo)"
    )

    # MANTENER: Campos legacy (para compatibilidad hacia atrás)
    product_id: Optional[int] = Field(
        0, ge=0, description="ID del producto (formato legacy, 0 = sin producto)"
    )
    product_qty: Optional[float] = Field(
        1, gt=0, description="Cantidad del producto (formato legacy)"
    )
    product_price: Optional[float] = Field(
        -1, description="Precio manual (formato legacy, -1 = usar pricelist)"
    )

    user_id: int = Field(
        0, ge=0, description="ID del vendedor (0 = balanceo automático)"
    )

    # NUEVOS CAMPOS ADICIONALES
    description: Optional[str] = Field(
        None, description="Descripción adicional del lead/cotización"
    )
    x_studio_producto: Optional[int] = Field(
        None, description="Campo custom de Odoo - ID del producto principal (entero)"
    )

    @field_validator("products")
    @classmethod
    def validate_products(cls, v, info):
        """Validar que al menos un método de agregar productos esté presente"""
        # Si viene products, debe tener al menos un elemento
        if v is not None and len(v) == 0:
            raise ValueError(
                "Si se especifica 'products', debe contener al menos un producto"
            )
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "description": "Formato simple (legacy) - Un solo producto",
                    "value": {
                        "partner_name": "Almacenes Torres",
                        "contact_name": "Luis Fernández",
                        "email": "luis@almacenes.com",
                        "phone": "+521234567890",
                        "lead_name": "Cotización Robot PUDU",
                        "product_id": 26174,
                        "product_qty": 2,
                    },
                },
                {
                    "description": "Formato múltiple (nuevo) - Varios productos diferentes",
                    "value": {
                        "partner_name": "Almacenes Torres",
                        "contact_name": "Luis Fernández",
                        "email": "luis@almacenes.com",
                        "phone": "+521234567890",
                        "lead_name": "Cotización Robots Mix",
                        "products": [
                            {"product_id": 26174, "qty": 2, "price": -1},
                            {"product_id": 26175, "qty": 1, "price": -1},
                        ],
                    },
                },
            ]
        }


class QuotationResponse(BaseModel):
    """Modelo para respuesta inmediata de cotización"""

    tracking_id: str
    status: str
    message: str
    estimated_time: str
    status_url: str


# Crear app FastAPI
api_app = FastAPI(
    title="MCP Odoo - API Asíncrona",
    description="API REST para operaciones asíncronas de Odoo",
    version="1.0.0",
)


def process_quotation_background(task_id: str, params: dict):
    """
    Procesa una cotización en background con reintentos automáticos.
    Esta función se ejecuta en un thread separado.
    """
    task = task_manager.get_task(task_id)
    if not task:
        return

    # Registrar inicio en log
    quotation_logger.log_quotation(
        tracking_id=task_id, input_data=params, status="started"
    )

    # Función interna que contiene toda la lógica de Odoo
    # Se aplicará el decorador de reintentos a esta función
    @retry_on_network_error(max_attempts=3, base_delay=2.0, backoff_factor=2.5)
    def execute_odoo_operations():
        """Ejecuta todas las operaciones de Odoo con reintentos automáticos"""

        # Marcar como en proceso
        task.start()
        task.update_progress("Iniciando cliente Odoo...")

        # Crear cliente
        client = DevOdooCRMClient()
        task.update_progress("Cliente Odoo conectado")

        # Buscar/crear partner
        task.update_progress("Verificando partner...")
        email_normalizado = params["email"].strip().lower()
        existing_partners = client.search_read(
            "res.partner",
            [("email", "=", email_normalizado)],
            ["id", "name"],
            limit=1,
        )

        if existing_partners:
            partner_id = existing_partners[0]["id"]
        else:
            partner_id = client.create(
                "res.partner",
                {
                    "name": params["contact_name"],
                    "email": email_normalizado,
                    "phone": params["phone"],
                    "is_company": False,
                },
            )

        task.update_progress("Partner verificado")

        # Asignar vendedor
        task.update_progress("Asignando vendedor...")
        assigned_user_id = params.get("user_id", 0)
        if not assigned_user_id:
            assigned_user_id = client.get_salesperson_with_least_opportunities()

        task.update_progress("Vendedor asignado")

        # Crear lead
        task.update_progress("Creando lead...")
        lead_values = {
            "name": params["lead_name"],
            "partner_name": params["partner_name"],
            "contact_name": params["contact_name"],
            "phone": params["phone"],
            "email_from": email_normalizado,
            "type": "lead",
            "partner_id": partner_id,
        }

        # Agregar descripción si existe
        if params.get("description"):
            lead_values["description"] = params["description"]

        # Agregar campo custom x_studio_producto
        # Si no se especifica, tomar el primer producto del array o el product_id legacy
        if params.get("x_studio_producto"):
            lead_values["x_studio_producto"] = params["x_studio_producto"]
        elif params.get("products") and len(params["products"]) > 0:
            # Auto-asignar el primer producto del array
            lead_values["x_studio_producto"] = params["products"][0]["product_id"]
        elif params.get("product_id", 0) > 0:
            # Usar el product_id legacy
            lead_values["x_studio_producto"] = params["product_id"]

        if assigned_user_id:
            lead_values["user_id"] = assigned_user_id

        lead_id = client.create("crm.lead", lead_values)
        task.update_progress("Lead creado")

        # Convertir a opportunity
        task.update_progress("Convirtiendo a oportunidad...")
        from datetime import datetime

        conversion_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        opportunity_values = {
            "type": "opportunity",
            "date_conversion": conversion_date,
            "stage_id": 3,
        }

        if assigned_user_id:
            opportunity_values["user_id"] = assigned_user_id

        client.write("crm.lead", lead_id, opportunity_values)
        task.update_progress("Convertido a oportunidad")

        # Crear sale order
        task.update_progress("Creando cotización...")
        sale_values = {
            "partner_id": partner_id,
            "opportunity_id": lead_id,
            "origin": params["lead_name"],
        }

        if assigned_user_id:
            sale_values["user_id"] = assigned_user_id

        sale_order_id = client.create("sale.order", sale_values)
        sale_data = client.read("sale.order", sale_order_id, ["name"])
        sale_order_name = sale_data.get("name", f"S{sale_order_id}")

        task.update_progress("Cotización creada")

        # Determinar qué productos agregar (nuevo formato vs legacy)
        products_to_add = []

        if params.get("products"):
            # Formato nuevo: array de productos
            task.update_progress(f"Agregando {len(params['products'])} producto(s)...")
            products_to_add = [
                {
                    "product_id": p["product_id"],
                    "qty": p.get("qty", 1.0),
                    "price": p.get("price", -1.0),
                }
                for p in params["products"]
            ]
        elif params.get("product_id", 0) > 0:
            # Formato legacy: un solo producto
            task.update_progress("Agregando producto...")
            products_to_add = [
                {
                    "product_id": params["product_id"],
                    "qty": params.get("product_qty", 1),
                    "price": params.get("product_price", -1),
                }
            ]

        # Agregar líneas de producto
        product_lines_info = []
        for idx, product_data in enumerate(products_to_add, 1):
            product_id = product_data["product_id"]
            product_qty = product_data["qty"]
            product_price = product_data["price"]

            line_values = {
                "order_id": sale_order_id,
                "product_id": product_id,
                "product_uom_qty": product_qty,
            }

            # Buscar precio si no se especificó
            if product_price <= 0:
                pricelist_items = client.search_read(
                    "product.pricelist.item",
                    [["pricelist_id", "=", 82], ["product_id", "=", product_id]],
                    ["fixed_price", "product_id"],
                    limit=1,
                )

                if pricelist_items:
                    price = pricelist_items[0].get("fixed_price", 0.0)
                    product_name = (
                        pricelist_items[0]["product_id"][1]
                        if pricelist_items[0].get("product_id")
                        else "Unknown"
                    )
                    line_values["price_unit"] = price
                    product_lines_info.append(
                        {
                            "product_id": product_id,
                            "product_name": product_name,
                            "qty": product_qty,
                            "price": price,
                            "source": "pricelist",
                        }
                    )
                else:
                    product_data_read = client.read(
                        "product.product", product_id, ["list_price", "name"]
                    )
                    price = product_data_read.get("list_price", 0.0)
                    product_name = product_data_read.get("name", "Unknown")
                    line_values["price_unit"] = price
                    product_lines_info.append(
                        {
                            "product_id": product_id,
                            "product_name": product_name,
                            "qty": product_qty,
                            "price": price,
                            "source": "product",
                        }
                    )
            else:
                # Precio manual
                line_values["price_unit"] = product_price
                # Obtener nombre del producto para el log
                product_data_read = client.read("product.product", product_id, ["name"])
                product_name = product_data_read.get("name", "Unknown")
                product_lines_info.append(
                    {
                        "product_id": product_id,
                        "product_name": product_name,
                        "qty": product_qty,
                        "price": product_price,
                        "source": "manual",
                    }
                )

            client.create("sale.order.line", line_values)

            if len(products_to_add) > 1:
                task.update_progress(f"Producto {idx}/{len(products_to_add)} agregado")

        if products_to_add:
            task.update_progress(f"✓ {len(products_to_add)} producto(s) agregado(s)")

        # Retornar resultado
        return {
            "partner_id": partner_id,
            "lead_id": lead_id,
            "opportunity_id": lead_id,
            "sale_order_id": sale_order_id,
            "sale_order_name": sale_order_name,
            "user_id": assigned_user_id,
            "products_added": product_lines_info,  # Nueva info detallada
            "product_line_note": (  # Legacy compatibility
                f"{len(product_lines_info)} producto(s) agregado(s)"
                if product_lines_info
                else None
            ),
        }

    try:
        # Ejecutar operaciones de Odoo con reintentos automáticos
        result = execute_odoo_operations()

        # Completar tarea con resultado
        task.complete(result)

        # Registrar resultado exitoso en log
        quotation_logger.update_quotation_log(
            tracking_id=task_id, output_data=result, status="completed"
        )

    except Exception as e:
        # Marcar como fallida
        error_msg = f"{type(e).__name__}: {str(e)}"
        task.fail(error_msg)

        # Registrar error en log
        quotation_logger.update_quotation_log(
            tracking_id=task_id, output_data=None, status="failed", error=error_msg
        )


@api_app.post("/api/quotation/async", response_model=QuotationResponse)
async def create_quotation_async(
    request: QuotationRequest, background_tasks: BackgroundTasks
):
    """
    Crea una cotización de forma asíncrona.
    Retorna inmediatamente con un tracking_id para consultar el estado.
    """
    # Generar tracking ID único
    task_id = f"quot_{uuid.uuid4().hex[:12]}"

    # Crear tarea
    task = task_manager.create_task(task_id, request.dict())

    # Agregar a background tasks
    background_tasks.add_task(process_quotation_background, task_id, request.dict())

    # Retornar respuesta inmediata
    return QuotationResponse(
        tracking_id=task_id,
        status="queued",
        message="Cotización en proceso. Consulte el estado con el tracking_id.",
        estimated_time="20-30 segundos",
        status_url=f"/api/quotation/status/{task_id}",
    )


@api_app.get("/api/quotation/status/{tracking_id}")
async def get_quotation_status(tracking_id: str):
    """
    Consulta el estado de una cotización asíncrona.
    """
    task = task_manager.get_task(tracking_id)

    if not task:
        raise HTTPException(
            status_code=404, detail=f"Tracking ID '{tracking_id}' no encontrado"
        )

    return JSONResponse(content=task.to_dict())


@api_app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "mcp-odoo-async"}


@api_app.get("/")
async def root():
    """Root endpoint con información del servicio"""
    return {
        "service": "MCP Odoo - API Asíncrona",
        "version": "1.0.0",
        "endpoints": {
            "create_quotation": "/api/quotation/async",
            "check_status": "/api/quotation/status/{tracking_id}",
            "handoff_whatsapp": "/api/elevenlabs/handoff",
            "health": "/api/health",
            "docs": "/docs",
        },
    }


# -----------------------------
# Modelo para Handoff WhatsApp
# -----------------------------


class HandoffRequest(BaseModel):
    """Modelo para solicitud de handoff desde ElevenLabs a WhatsApp"""

    user_phone: str = Field(
        ..., description="Teléfono del usuario que solicita atención"
    )
    reason: str = Field("Solicita atención humana", description="Motivo del handoff")
    conversation_id: Optional[str] = Field(
        None, description="ID de la conversación en ElevenLabs"
    )
    user_name: Optional[str] = Field(None, description="Nombre del usuario")
    additional_context: Optional[str] = Field(
        None, description="Contexto adicional de la conversación"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_phone": "+5215512345678",
                "reason": "Cliente desea hablar con un vendedor",
                "conversation_id": "conv_abc123",
                "user_name": "Juan Pérez",
            }
        }
