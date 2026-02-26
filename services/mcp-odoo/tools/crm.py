# tools/crm.py
"""
DESARROLLO (Lectura y Escritura):
- dev_create_quotation: Crea un flujo completo: partner → lead → oportunidad → cotización
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import os
from datetime import datetime
from core.tasks import TaskStatus
import unicodedata
import re


def normalize_email(email: str) -> str:
    """
    Normaliza y limpia un email eliminando acentos, espacios y caracteres inválidos.
    Corrige automáticamente errores comunes.

    Args:
        email: Email a normalizar

    Returns:
        Email normalizado y corregido en minúsculas sin acentos

    Raises:
        ValueError: Si el email no tiene el formato mínimo requerido (usuario@dominio)

    Example:
        normalize_email("López@Gmail.com") -> "lopez@gmail.com"
        normalize_email("aguilar@gmail.com7") -> "aguilar@gmail.com"
        normalize_email("test@test.co1m") -> "test@test.com"
    """
    # Guardar original para logs
    original = email

    # Eliminar espacios al inicio y final
    email = email.strip()

    # Convertir a minúsculas
    email = email.lower()

    # Eliminar acentos y diacríticos
    email = unicodedata.normalize("NFKD", email)
    email = email.encode("ASCII", "ignore").decode("ASCII")

    # Eliminar espacios internos que puedan quedar
    email = email.replace(" ", "")
    email = email.replace(",", "")

    # Intentos de corrección y normalización en cadena
    # 1) Si hay múltiples @, conservar el primero y concatenar el resto
    if email.count("@") > 1:
        parts = email.split("@")
        user = parts[0]
        domain = "".join(parts[1:])
        email = f"{user}@{domain}"

    # 2) Si no hay @, intentar inferirlo reemplazando el primer punto por @ (heurística)
    if email.count("@") == 0:
        if "." in email:
            idx = email.find(".")
            user = email[:idx]
            domain = email[idx + 1 :]
            email = f"{user}@{domain}"
        else:
            # No se puede inferir, fallback al email genérico
            fallback = "emailinvalido@corporativosade.com.mx"
            print(f"⚠️ Email inválido '{original}' -> usando fallback '{fallback}'")
            return fallback

    # A partir de aquí deberíamos tener 1 @
    if email.count("@") != 1:
        fallback = "emailinvalido@corporativosade.com.mx"
        print(f"⚠️ Email inválido '{original}' -> usando fallback '{fallback}'")
        return fallback

    user, domain = email.split("@", 1)

    # Usuario no puede estar vacío
    if not user:
        fallback = "emailinvalido@corporativosade.com.mx"
        print(
            f"⚠️ Email inválido '{original}' (usuario vacío) -> usando fallback '{fallback}'"
        )
        return fallback

    # CORRECCIÓN AUTOMÁTICA: Eliminar números al final de la extensión
    domain = re.sub(r"(\.[a-zA-Z]+)\d+$", r"\1", domain)

    # CORRECCIÓN AUTOMÁTICA: Arreglar números mezclados en la extensión
    domain = re.sub(r"\.([a-zA-Z]+)\d+([a-zA-Z]+)$", r".\1\2", domain)

    # Si el dominio no tiene punto, intentar añadir .com
    if "." not in domain:
        domain_candidate = domain + ".com"
        email_candidate = f"{user}@{domain_candidate}"
        email_pattern = r"^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if re.match(email_pattern, email_candidate):
            domain = domain_candidate
        else:
            fallback = "emailinvalido@corporativosade.com.mx"
            print(
                f"⚠️ Email '{original}' no pudo ser corregido -> usando fallback '{fallback}'"
            )
            return fallback

    # Reconstruir email limpio
    email_clean = f"{user}@{domain}"

    # Validación final del formato
    email_pattern = r"^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(email_pattern, email_clean):
        fallback = "emailinvalido@corporativosade.com.mx"
        print(
            f"⚠️ Email '{original}' inválido después de limpieza -> usando fallback '{fallback}'"
        )
        return fallback

    # Log si se hizo corrección
    if original != email_clean:
        print(f"📧 Email corregido: '{original}' -> '{email_clean}'")

    return email_clean


class QuotationResult(BaseModel):
    """Modelo para el resultado de crear una cotización."""

    partner_id: int
    partner_name: str
    lead_id: int
    lead_name: str
    opportunity_id: int
    opportunity_name: str
    sale_order_id: int
    sale_order_name: str
    environment: str = "development"
    steps: Dict[str, str]


class DevOdooCRMClient:
    """
    Cliente Odoo específico para el ambiente de DESARROLLO (CRM/Cotizaciones).
    Se conecta a: pegasuscontrol-dev18-25468489.dev.odoo.com
    """

    def __init__(self):
        import xmlrpc.client

        # Configuración específica para DESARROLLO
        self.url = os.environ.get(
            "DEV_ODOO_URL", "https://pegasuscontrol-dev18-25468489.dev.odoo.com"
        ).rstrip("/")
        self.db = os.environ.get("DEV_ODOO_DB", "pegasuscontrol-dev18-25468489")
        self.username = os.environ.get("DEV_ODOO_LOGIN")
        self.password = os.environ.get("DEV_ODOO_API_KEY")

        if not self.username or not self.password:
            raise ValueError(
                "Faltan credenciales DEV_ODOO_LOGIN o DEV_ODOO_API_KEY en .env"
            )

        # Conexión XML-RPC a desarrollo con allow_none=True para manejar valores None
        self.common = xmlrpc.client.ServerProxy(
            f"{self.url}/xmlrpc/2/common", allow_none=True
        )
        self.models = xmlrpc.client.ServerProxy(
            f"{self.url}/xmlrpc/2/object", allow_none=True
        )

        # Autenticación
        self.uid = self.common.authenticate(self.db, self.username, self.password, {})

        if not self.uid:
            raise ValueError("No se pudo autenticar en el ambiente de desarrollo")

    def execute_kw(self, model: str, method: str, args=None, kwargs=None):
        """Ejecuta un método en el modelo especificado."""
        args = args or []
        kwargs = kwargs or {}
        return self.models.execute_kw(
            self.db, self.uid, self.password, model, method, args, kwargs
        )

    def search_read(
        self, model: str, domain: list, fields: list, limit: int = 1
    ) -> list:
        """Busca y lee registros."""
        return self.execute_kw(
            model, "search_read", [domain], {"fields": fields, "limit": limit}
        )

    def create(self, model: str, values: Dict[str, Any]) -> int:
        """Crea un nuevo registro."""
        return self.execute_kw(model, "create", [values])

    def write(self, model: str, record_id: int, values: Dict[str, Any]) -> bool:
        """Actualiza un registro existente."""
        return self.execute_kw(model, "write", [[record_id], values])

    def read(self, model: str, record_id: int, fields: list = None) -> Dict[str, Any]:
        """Lee un registro por ID."""
        fields = fields or []
        result = self.execute_kw(model, "read", [[record_id]], {"fields": fields})
        return result[0] if result else {}

    def action_set_won(self, lead_id: int) -> bool:
        """Marca una oportunidad como ganada."""
        return self.execute_kw("crm.lead", "action_set_won", [[lead_id]])

    def get_salesperson_with_least_opportunities(self) -> int | None:
        """
        Obtiene el ID del vendedor (user) con menos oportunidades activas.

        Criterios:
        - Obtiene miembros de los equipos de ventas (ID 1 y 14)
        - Solo cuenta oportunidades activas (type='opportunity')
        - Solo cuenta oportunidades en etapas específicas (1, 2, 10, 3)
        - Retorna el user_id con menor cantidad de oportunidades activas

        Returns:
            int: ID del vendedor con menos carga, o None si no hay vendedores
        """
        # 1. Obtener miembros de los equipos de ventas (ID 1 y 14)
        teams = self.search_read(
            "crm.team",
            [("id", "in", [14])],  # 14 es el equipo de ventas servibot
            ["member_ids"],
        )

        members_ids = set()
        for team in teams:
            members_ids.update(team.get("member_ids", []))

        members_ids = list(members_ids)

        if not members_ids:
            return None

        # 2. Inicializar contador para TODOS los miembros del equipo
        # Primero obtenemos los nombres de todos los miembros
        users_info = self.search_read(
            "res.users",
            [("id", "in", members_ids)],
            ["id", "name"],
            limit=len(members_ids),  # Asegurar que obtenemos TODOS los miembros
        )

        # Ordenar por ID para orden determinístico
        users_info_sorted = sorted(users_info, key=lambda u: u["id"])

        opportunities_by_user = {}
        for user in users_info_sorted:
            opportunities_by_user[user["id"]] = {
                "name": user["name"],
                "count": 0,
            }  # 3. Obtener todas las oportunidades activas en etapas específicas
        leads = self.search_read(
            "crm.lead",
            [
                ("stage_id", "in", [1, 2, 10, 3]),
                ("active", "=", True),
                ("type", "=", "opportunity"),
            ],
            ["user_id"],
            limit=None,  # Sin límite para obtener todas
        )

        # 4. Contar oportunidades activas por vendedor
        for lead in leads:
            user_info = lead.get("user_id")

            # Filtrar solo usuarios que están en los equipos
            if not user_info or user_info[0] not in members_ids:
                continue

            user_id = user_info[0]

            # Incrementar el contador (ya está inicializado)
            if user_id in opportunities_by_user:
                opportunities_by_user[user_id]["count"] += 1

        # 5. Encontrar el vendedor con menos oportunidades
        if not opportunities_by_user:
            return None

        # Usar el count como criterio principal y el user_id como desempate (menor ID gana)
        least_user_id = min(
            opportunities_by_user,
            key=lambda uid: (opportunities_by_user[uid]["count"], uid),
        )

        return least_user_id


def register(mcp, deps: dict):
    """
    Registra las herramientas MCP para CRM y Cotizaciones.

    DESARROLLO (Lectura y Escritura):
    - dev_create_quotation: Flujo completo para crear cotización desde lead
    """
    # Cliente de PRODUCCIÓN (desde deps)
    prod_client = deps["odoo"]

    # Cliente de DESARROLLO - lazy loading
    dev_client = None

    def get_dev_client():
        """Inicializa el cliente de desarrollo solo cuando se necesita."""
        nonlocal dev_client
        if dev_client is None:
            dev_client = DevOdooCRMClient()
        return dev_client

    def get_odoo_client():
        """Retorna el cliente de Odoo según el ambiente configurado."""
        import os

        environment = os.getenv("ODOO_ENVIRONMENT", "dev").lower()
        print(f"[CRM Tool] 🌍 Ambiente detectado: {environment}")
        if environment == "prod":
            print(f"[CRM Tool] 📊 Usando cliente de PRODUCCIÓN")
            return prod_client
        else:
            print(f"[CRM Tool] 🔧 Usando cliente de DESARROLLO")
            return get_dev_client()

    @mcp.tool(
        name="dev_create_quotation",
        description="Crea una cotización completa de forma ASÍNCRONA con tracking y logging S3. Retorna tracking_id para consultar estado después. Para obtener el resultado completo, usar dev_get_quotation_status con el tracking_id retornado.",
    )
    def dev_create_quotation(
        partner_name: str,
        contact_name: str,
        email: str,
        phone: str,
        lead_name: str,
        ciudad: Optional[str] = None,
        user_id: int = 0,
        product_id: int = 0,
        product_qty: float = 1.0,
        product_price: float = -1.0,
        products: Optional[List[dict]] = None,
        description: Optional[str] = None,
        x_studio_producto: Optional[int] = None,
    ) -> dict:
        """
        Crea una cotización completa DESDE CERO de forma ASÍNCRONA.

        ✨ NUEVA ARQUITECTURA (Service Layer Pattern):
        - Usa QuotationService para lógica de negocio
        - Elimina código duplicado con endpoints HTTP
        - Retorna tracking_id inmediatamente
        - LLM consulta estado con dev_get_quotation_status()

        Flujo completo (ejecutado en background):
        1. Verifica/crea partner por email
        2. Asigna vendedor automáticamente (balanceo)
        3. Crea lead nuevo
        4. Convierte a oportunidad
        5. Genera orden de venta
        6. Agrega productos

        Args:
            partner_name: Nombre del cliente/empresa
            contact_name: Nombre del contacto
            email: Email del contacto
            phone: Teléfono del contacto
            lead_name: Nombre del lead/oportunidad
            ciudad: Ciudad del contacto (opcional)
            user_id: ID del vendedor (0 = asignación automática)
            product_id: ID del producto [LEGACY]
            product_qty: Cantidad [LEGACY]
            product_price: Precio manual [LEGACY]
            products: Lista [{"product_id": int, "qty": float, "price": float}]
            description: Descripción del lead
            x_studio_producto: Producto principal (Many2one)

        Returns:
            dict con tracking_id, status, mode="create", message

        Ejemplo:
            dev_create_quotation(
                partner_name="ACME Corp",
                contact_name="John Doe",
                email="john@acme.com",
                phone="+1234567890",
                lead_name="Restaurant Equipment",
                products=[
                    {"product_id": 26156, "qty": 10, "price": 9350.0}
                ]
            )
        """
        # Importar servicio
        from core.quotation_service import QuotationService

        # Obtener cliente Odoo
        client = get_odoo_client()

        # Crear servicio
        service = QuotationService(client)

        # Delegar al servicio
        return service.create_from_scratch(
            partner_name=partner_name,
            contact_name=contact_name,
            email=email,
            phone=phone,
            lead_name=lead_name,
            ciudad=ciudad,
            user_id=user_id,
            product_id=product_id,
            product_qty=product_qty,
            product_price=product_price,
            products=products,
            description=description,
            x_studio_producto=x_studio_producto,
        )

    @mcp.tool(
        name="dev_get_quotation_status",
        description="Consulta el estado de una cotización asíncrona usando su tracking_id. Retorna el estado actual (queued/processing/completed/failed) y el resultado si está disponible.",
    )
    def dev_get_quotation_status(tracking_id: str) -> dict:
        """
        Consulta el estado de una cotización creada con dev_create_quotation.

        Args:
            tracking_id: ID de seguimiento retornado por dev_create_quotation

        Returns:
            dict con status, progress, result (si completed), error (si failed)

        Ejemplo retorno (en proceso):
            {
                "tracking_id": "quot_abc123",
                "status": "processing",
                "progress": "Creando lead...",
                "created_at": "2025-12-22T10:48:40"
            }

        Ejemplo retorno (completado):
            {
                "tracking_id": "quot_abc123",
                "status": "completed",
                "result": {
                    "partner_id": 123,
                    "lead_id": 456,
                    "sale_order_id": 789,
                    "sale_order_name": "S00123",
                    "steps": {...}
                },
                "created_at": "2025-12-22T10:48:40",
                "updated_at": "2025-12-22T10:49:10"
            }
        """
        from core.tasks import task_manager

        task = task_manager.get_task(tracking_id)

        if not task:
            return {
                "tracking_id": tracking_id,
                "status": "not_found",
                "error": f"No se encontró tarea con tracking_id: {tracking_id}",
            }

        response = {
            "tracking_id": task.id,  # FIX: era task.task_id
            "status": (
                task.status.value if hasattr(task.status, "value") else str(task.status)
            ),
            "created_at": task.created_at.isoformat(),
        }

        # Agregar progreso si existe
        if task.progress:
            response["progress"] = task.progress

        # Agregar tiempo transcurrido
        response["elapsed_time"] = f"{task.elapsed_seconds():.2f}s"

        # Agregar completed_at si terminó
        if task.completed_at:
            response["completed_at"] = task.completed_at.isoformat()

        # Agregar resultado si completó exitosamente
        if task.status == TaskStatus.COMPLETED and task.result:
            response["result"] = task.result
            response["success"] = True  # Para ElevenLabs

        # Agregar error si falló
        if task.status == TaskStatus.FAILED and task.error:
            response["error"] = task.error
            response["success"] = False  # Para ElevenLabs

        return response

    @mcp.tool(
        name="dev_update_lead_quotation",
        description="Actualiza un lead EXISTENTE y crea una cotización a partir de él. Usa esta herramienta cuando ya tengas un lead_id y quieras actualizarlo + generar cotización.",
    )
    def dev_update_lead_quotation(
        lead_id: int,
        products: Optional[List[dict]] = None,
        product_id: int = 0,
        product_qty: float = 1.0,
        product_price: float = -1.0,
        update_lead_data: Optional[dict] = None,
        description: Optional[str] = None,
        x_studio_producto: Optional[int] = None,
    ) -> dict:
        """
        Actualiza un lead EXISTENTE y crea una cotización a partir de él.

        ✨ NUEVA HERRAMIENTA (Service Layer Pattern):
        - Separada de dev_create_quotation para claridad
        - Usa QuotationService compartido
        - Retorna tracking_id para seguimiento asíncrono

        DIFERENCIAS vs dev_create_quotation:
        - ❌ NO crea partner nuevo
        - ❌ NO crea lead nuevo
        - ✅ Lee lead existente
        - ✅ Actualiza campos del lead (opcional)
        - ✅ Convierte a oportunidad (si no lo es)
        - ✅ Crea orden de venta + productos

        Flujo (ejecutado en background):
        1. Lee lead existente por lead_id
        2. Actualiza campos del lead (opcional)
        3. Convierte a oportunidad (si no lo es)
        4. Crea orden de venta
        5. Agrega productos

        Args:
            lead_id: ID del lead existente (OBLIGATORIO, debe ser > 0)
            products: Lista [{"product_id": int, "qty": float, "price": float}]
            product_id: ID del producto [LEGACY]
            product_qty: Cantidad [LEGACY]
            product_price: Precio manual [LEGACY]
            update_lead_data: Dict con campos a actualizar
                Ejemplo: {"description": "Nuevo texto", "city": "CDMX", "priority": 3}
            description: Descripción adicional
            x_studio_producto: Producto principal (Many2one)

        Returns:
            dict con tracking_id, status, mode="update", lead_id, message

        Ejemplo:
            dev_update_lead_quotation(
                lead_id=12345,
                products=[
                    {"product_id": 26156, "qty": 5, "price": 9000.0}
                ],
                update_lead_data={
                    "description": "Cliente solicitó cambio de cantidad",
                    "priority": "2"
                }
            )
        """
        # Validar lead_id
        if not lead_id or lead_id <= 0:
            return {
                "error": "lead_id es obligatorio y debe ser mayor a 0",
                "example": "dev_update_lead_quotation(lead_id=12345, products=[...])",
            }

        # Importar servicio
        from core.quotation_service import QuotationService

        # Obtener cliente Odoo
        client = get_odoo_client()

        # Crear servicio
        service = QuotationService(client)

        # Delegar al servicio
        return service.create_from_existing_lead(
            lead_id=lead_id,
            products=products,
            product_id=product_id,
            product_qty=product_qty,
            product_price=product_price,
            update_lead_data=update_lead_data,
            description=description,
            x_studio_producto=x_studio_producto,
        )
