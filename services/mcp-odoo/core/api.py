"""
API REST con FastAPI para operaciones asíncronas.
Endpoints para crear cotizaciones en background y consultar su estado.
"""

import uuid
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional

from core.tasks import task_manager, QuotationTask
from core.logger import quotation_logger
from tools.crm import DevOdooCRMClient


# Modelos Pydantic para validación
class QuotationRequest(BaseModel):
    """Modelo para solicitud de cotización"""

    partner_name: str = Field(..., description="Nombre de la empresa/cliente")
    contact_name: str = Field(..., description="Nombre del contacto")
    email: str = Field(..., description="Email del contacto")
    phone: str = Field(..., description="Teléfono del contacto")
    lead_name: str = Field(..., description="Nombre/descripción del lead")
    product_id: int = Field(0, ge=0, description="ID del producto (0 = sin producto)")
    product_qty: int = Field(1, ge=1, description="Cantidad del producto")
    product_price: float = Field(-1, description="Precio manual (-1 = usar pricelist)")
    user_id: int = Field(
        0, ge=0, description="ID del vendedor (0 = balanceo automático)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "partner_name": "Almacenes Torres",
                "contact_name": "Luis Fernández",
                "email": "luis@almacenes.com",
                "phone": "+521234567890",
                "lead_name": "Cotización Robot PUDU",
                "product_id": 26174,
                "product_qty": 2,
            }
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
    Procesa una cotización en background.
    Esta función se ejecuta en un thread separado.
    """
    task = task_manager.get_task(task_id)
    if not task:
        return

    # Registrar inicio en log
    quotation_logger.log_quotation(
        tracking_id=task_id, input_data=params, status="started"
    )

    try:
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

        # Agregar línea de producto si se especificó
        product_line_note = None
        if params.get("product_id", 0) > 0:
            task.update_progress("Agregando producto...")

            product_id = params["product_id"]
            product_qty = params.get("product_qty", 1)
            product_price = params.get("product_price", -1)

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
                    product_line_note = (
                        f"Precio del Pricelist para '{product_name}': ${price}"
                    )
                else:
                    product_data = client.read(
                        "product.product", product_id, ["list_price", "name"]
                    )
                    price = product_data.get("list_price", 0.0)
                    product_name = product_data.get("name", "Unknown")
                    line_values["price_unit"] = price
                    product_line_note = (
                        f"Precio del producto '{product_name}': ${price}"
                    )
            else:
                line_values["price_unit"] = product_price
                product_line_note = f"Precio manual: ${product_price}"

            client.create("sale.order.line", line_values)
            task.update_progress("Producto agregado")

        # Completar tarea con resultado
        result = {
            "partner_id": partner_id,
            "lead_id": lead_id,
            "opportunity_id": lead_id,
            "sale_order_id": sale_order_id,
            "sale_order_name": sale_order_name,
            "user_id": assigned_user_id,
            "product_line_note": product_line_note,
        }

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
            "health": "/api/health",
            "docs": "/docs",
        },
    }
