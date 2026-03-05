"""
Servicio para envío masivo de emails a leads.
Procesamiento por batches con threading no-bloqueante.

🔗 FUENTE DE DATOS:
    - Ambiente Odoo controlado por variable ODOO_ENVIRONMENT (dev/production)
    - OdooClient detecta automáticamente el ambiente
"""

import os
import time
import uuid
import threading
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from core.odoo_client import OdooClient
from core.email_logger import email_logger


class BulkEmailService:
    """Gestiona el envío masivo de emails con control de intentos y batching"""

    def __init__(self):
        """
        Inicializa el servicio de email masivo.

        El ambiente Odoo (dev/production) se detecta automáticamente desde
        la variable de entorno ODOO_ENVIRONMENT en OdooClient.
        """
        # Cliente Odoo detecta automáticamente ODOO_ENVIRONMENT
        self.odoo_client = OdooClient()
        self.jobs: Dict[str, Dict[str, Any]] = {}  # job_id -> job_info
        self.jobs_lock = threading.Lock()

        # URLs de las lambdas
        self.lambda_odoo_url = os.getenv("LAMBDA_ODOO_SUPERVISOR_URL")
        self.lambda_email_url = os.getenv("LAMBDA_EMAIL_SENDER_URL")

        # Configuración de batches
        self.batch_size = int(os.getenv("EMAIL_BATCH_SIZE", "15"))
        self.batch_delay = int(os.getenv("EMAIL_BATCH_DELAY_SECONDS", "7"))

        if not self.lambda_odoo_url or not self.lambda_email_url:
            raise ValueError(
                "Faltan variables de entorno: LAMBDA_ODOO_SUPERVISOR_URL o LAMBDA_EMAIL_SENDER_URL"
            )

        odoo_env = os.getenv("ODOO_ENVIRONMENT", "dev")
        print(
            f"✅ BulkEmailService inicializado (batch_size={self.batch_size}, odoo={odoo_env})"
        )

    def get_leads(
        self,
        environment: str = "dev",
        lead_ids: Optional[List[int]] = None,
        domain: Optional[List] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Obtiene leads según la estrategia de búsqueda.

        🔗 FUENTE DE DATOS:
            - Ambiente Odoo controlado por ODOO_ENVIRONMENT (dev/production)
            - Ignora el parámetro 'environment' (legacy, mantener por compatibilidad)

        PRIORIDAD DE BÚSQUEDA:
            1. lead_ids → IDs específicos (ignora filters y domain)
            2. filters → Filtros personalizados (days_ago, stage_id, user_id)
            3. default → Filtro automático (>5 días, team_id=14, stage_id=1, sin actividad)

        FILTRO DEFAULT (sin parámetros):
            - create_date > 5 días
            - team_id = 14 (Ventas servibot)
            - stage_id = 1 (Nueva - Recien captada)
            - Sin actividad humana (solo mensajes de bots: Lexi Aria, OdooBot)

        Args:
            environment: DEPRECADO - Usar ODOO_ENVIRONMENT variable de entorno
            lead_ids: Lista de IDs específicos a buscar
            domain: DEPRECADO - Usar filters
            filters: Filtros personalizados (days_ago, stage_id, user_id)

        Returns:
            Lista de leads con id, name, partner_id, user_id, email_from, phone

        Ejemplos:
            # IDs específicos
            get_leads(lead_ids=[31697, 31698])

            # Filtros personalizados
            get_leads(filters={"days_ago": 10, "stage_id": 1, "user_id": 5})

            # Default (filtro automático)
            get_leads()
        """
        # PRIORIDAD 1: IDs específicos
        if lead_ids:
            final_domain = [["id", "in", lead_ids], ["type", "=", "lead"]]
            search_type = f"IDs específicos ({len(lead_ids)} leads)"

        # PRIORIDAD 2: Filtros personalizados
        elif filters:
            final_domain = []

            # Filtro: días atrás
            if "days_ago" in filters:
                days_ago = (
                    datetime.now() - timedelta(days=filters["days_ago"])
                ).strftime("%Y-%m-%d")
                final_domain.append(["create_date", ">=", days_ago])

            # Filtro: stage_id
            if "stage_id" in filters:
                final_domain.append(["stage_id", "=", filters["stage_id"]])

            # Filtro: user_id
            if "user_id" in filters:
                final_domain.append(["user_id", "=", filters["user_id"]])

            # Filtro: team_id
            if "team_id" in filters:
                final_domain.append(["team_id", "=", filters["team_id"]])
            # Asegurar que se filtren solo records de tipo 'lead' a menos que se especifique otro tipo
            if "type" in filters:
                final_domain.append(["type", "=", filters["type"]])
            else:
                final_domain.append(["type", "=", "lead"])

            search_type = f"filtros personalizados ({len(final_domain)} condiciones)"

        # PRIORIDAD 3: Filtro default (automático)
        else:
            # Filtro default: leads antiguos (más de 5 días) del equipo Ventas servibot con stage "Nueva (Recien captada)"
            five_days_ago = (datetime.now() - timedelta(days=5)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            final_domain = [
                ["create_date", "<=", five_days_ago],
                ["team_id", "=", 14],  # Ventas servibot
                ["stage_id", "=", 1],  # Nueva (Recien captada)
                ["type", "=", "lead"],
            ]
            search_type = f"filtro default (>5 días, team_id=14, stage_id=1, create_date<={five_days_ago})"

        fields = ["id", "name", "partner_id", "user_id", "email_from", "phone"]

        try:
            # Obtener todos los leads que cumplan el filtro
            leads = self.odoo_client.search_read(
                "crm.lead", final_domain, fields, limit=5000
            )
            odoo_env = os.getenv("ODOO_ENVIRONMENT", "dev")
            print(
                f"📋 Obtenidos {len(leads)} leads iniciales (Odoo {odoo_env.upper()}, búsqueda: {search_type})"
            )

            # Filtrar leads sin actividad real (solo aplica al filtro default)
            if not lead_ids and not filters:
                leads = self._filter_leads_without_activity(leads)
                print(f"📋 Filtrados {len(leads)} leads SIN actividad humana")

            return leads
        except Exception as e:
            print(f"❌ Error obteniendo leads: {e}")
            return []

    def _filter_leads_without_activity(
        self, leads: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filtra leads que NO tienen actividad humana real en el chatter.

        🤖 DETECCIÓN DE ACTIVIDAD:
            - Mensajes de BOTS (Lexi Aria ID 109061, OdooBot ID 106917) = NO actividad
            - Mensajes de HUMANOS (cualquier otro author_id) = SÍ actividad
            - Attachments de HUMANOS = SÍ actividad
            - Attachments de BOTS = NO actividad

        Un lead SIN actividad SOLO tiene:
            - Mensajes automáticos de Lexi Aria (ID 109061)
            - Mensajes automáticos de OdooBot (ID 106917)
            - Mensajes de sistema sin contenido

        Cualquier mensaje o attachment de un humano = actividad → lead excluido

        Args:
            leads: Lista de leads a filtrar

        Returns:
            Lista de leads sin actividad humana
        """
        print("🚀 Filtrando leads sin actividad humana (BULK PROCESSING)...")

        # IDs de bots automáticos según ambiente (mensajes de estos usuarios = NO actividad)
        odoo_env = os.getenv("ODOO_ENVIRONMENT", "dev").lower()

        if odoo_env in ["prod", "production"]:
            # PRODUCCIÓN: OdooBot ID 2, Lexi Aria ID 109061
            BOT_AUTHOR_IDS = [2, 109061]
            print(f"   🤖 Bots PRODUCCIÓN: OdooBot (2), Lexi Aria (109061)")
        else:
            # DESARROLLO: OdooBot ID 106917, Lexi Aria ID 109061
            BOT_AUTHOR_IDS = [106917, 109061]
            print(f"   🤖 Bots DESARROLLO: OdooBot (106917), Lexi Aria (109061)")

        # PASO 1: Obtener todos los leads con message_ids
        lead_ids = [lead["id"] for lead in leads]

        leads_with_messages = self.odoo_client.search_read(
            "crm.lead",
            [["id", "in", lead_ids]],
            ["id", "message_ids"],
            limit=len(lead_ids),
        )

        # PASO 2: Recolectar TODOS los message_ids
        lead_messages_map = {}
        all_message_ids = []

        for lead_data in leads_with_messages:
            lead_id = lead_data["id"]
            message_ids = lead_data.get("message_ids", [])
            lead_messages_map[lead_id] = message_ids
            all_message_ids.extend(message_ids)

        print(f"   📧 Total mensajes a analizar: {len(all_message_ids)}")

        # PASO 3: Obtener TODOS los mensajes en batches
        batch_size = 500
        all_messages = []

        for i in range(0, len(all_message_ids), batch_size):
            batch_ids = all_message_ids[i : i + batch_size]

            messages = self.odoo_client.search_read(
                "mail.message",
                [["id", "in", batch_ids]],
                ["id", "body", "message_type", "attachment_ids", "author_id"],
                limit=len(batch_ids),
            )

            all_messages.extend(messages)

        print(f"   💾 Total mensajes obtenidos: {len(all_messages)}")

        # PASO 4: Indexar mensajes por ID
        messages_by_id = {msg["id"]: msg for msg in all_messages}

        # PASO 5: Filtrar leads sin actividad humana
        filtered_leads = []
        excluded_count = 0

        for lead in leads:
            lead_id = lead["id"]
            message_ids = lead_messages_map.get(lead_id, [])

            # Si no tiene mensajes, NO tiene actividad
            if not message_ids:
                filtered_leads.append(lead)
                continue

            has_activity = False

            for msg_id in message_ids:
                msg = messages_by_id.get(msg_id)
                if not msg:
                    continue

                author_id = (
                    msg.get("author_id", [False])[0] if msg.get("author_id") else False
                )
                attachment_ids = msg.get("attachment_ids", [])

                # Attachments de humanos = actividad
                if (
                    attachment_ids
                    and len(attachment_ids) > 0
                    and author_id not in BOT_AUTHOR_IDS
                ):
                    has_activity = True
                    break

                # Mensajes de humanos con contenido = actividad
                if author_id and author_id not in BOT_AUTHOR_IDS:
                    body = msg.get("body", "") or ""
                    import re

                    body_clean = re.sub(r"<[^>]+>", "", body).strip()

                    if body_clean:
                        has_activity = True
                        break

            if has_activity:
                excluded_count += 1
            else:
                filtered_leads.append(lead)

        print(f"   ✅ Leads sin actividad humana: {len(filtered_leads)}")
        print(f"   ❌ Leads excluidos (con actividad): {excluded_count}")

        return filtered_leads

    def check_lead_attempts(self, lead_id: int) -> Dict[str, Any]:
        """
        Consulta los intentos de un lead en Odoo vía Lambda.

        Args:
            lead_id: ID del lead

        Returns:
            {
                "lead_id": int,
                "attempts": int,
                "can_send": bool,
                "error": str | None
            }
        """
        try:
            # Lambda espera formato: {"function": "...", "params": {...}}
            response = requests.post(
                self.lambda_odoo_url,
                json={
                    "function": "get_lead_last_attempt",
                    "params": {"lead_id": lead_id},
                },
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            # Lambda retorna: {"attempt_number": X, ...}
            attempts = data.get("attempt_number", 0)
            can_send = attempts < 3

            return {
                "lead_id": lead_id,
                "attempts": attempts,
                "can_send": can_send,
                "error": None,
            }
        except Exception as e:
            print(f"⚠️  Error verificando intentos para lead {lead_id}: {e}")
            return {
                "lead_id": lead_id,
                "attempts": 0,
                "can_send": False,
                "error": str(e),
            }

    def send_email_to_lead(
        self, lead: Dict[str, Any], attempt_number: int
    ) -> Dict[str, Any]:
        """
        Envía un email a un lead vía Lambda.

        Args:
            lead: Diccionario con datos del lead
            attempt_number: Número de intento actual (1, 2 o 3)

        Returns:
            {
                "lead_id": int,
                "status": "success" | "error",
                "message": str
            }
        """
        lead_id = lead["id"]
        email = lead.get("email_from") or lead.get("partner_id", [None, None])[1]
        name = lead.get("name", "Lead")

        if not email:
            return {
                "lead_id": lead_id,
                "status": "error",
                "message": "Lead sin email",
            }

        try:
            # Lambda espera formato: {"function": "...", "params": {...}}
            body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f0f4f8; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 30px auto; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.08); }}
        .header {{ background: #000000; padding: 25px; text-align: center; }}
        .header img {{ max-width: 160px; }}
        .hero {{ background: linear-gradient(135deg, #0052cc 0%, #002d72 100%); color: white; padding: 50px 30px; text-align: center; }}
        .hero h1 {{ margin: 0; font-size: 26px; font-weight: 700; line-height: 1.2; }}
        .hero p {{ opacity: 0.9; font-size: 16px; margin-top: 10px; }}
        .content {{ padding: 40px; color: #2d3748; line-height: 1.6; }}
        .lead-info {{ background: #ebf4ff; border-radius: 8px; padding: 15px; margin: 25px 0; font-size: 13px; color: #2b6cb0; border: 1px solid #bee3f8; }}
        .highlight {{ color: #0052cc; font-weight: bold; }}
        .benefits {{ list-style: none; padding: 0; margin: 25px 0; }}
        .benefits li {{ margin-bottom: 12px; display: flex; align-items: center; font-size: 15px; }}
        .benefits li::before {{ content: '🤖'; margin-right: 10px; }}
        .cta-container {{ text-align: center; margin-top: 35px; }}
        .btn-whatsapp {{ display: inline-block; background-color: #25D366; color: #ffffff !important; text-decoration: none; padding: 16px 30px; border-radius: 50px; font-weight: bold; font-size: 16px; box-shadow: 0 4px 12px rgba(37, 211, 102, 0.3); transition: 0.3s; }}
        .reply-text {{ margin-top: 20px; font-size: 14px; color: #718096; }}
        .footer {{ background: #f7fafc; padding: 25px; text-align: center; font-size: 12px; color: #a0aec0; border-top: 1px solid #edf2f7; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="https://www.servibot.mx/web/image/website/7/logo?unique=fcb79f9" alt="Servibot">
        </div>

        <div class="hero">
            <h1>¿Llevamos tu servicio al futuro?</h1>
            <p>Tu solución Servibot está a un clic de distancia.</p>
        </div>

        <div class="content">
            <p>Hola <strong>{name}</strong>,</p>
            <p>Seguimos impulsando la innovación en México y queremos que seas parte de ello. Vimos tu interés en nuestras soluciones de <strong>robótica inteligente</strong> y no queremos que pierdas la oportunidad de transformar tu operación.</p>
            
            <div class="lead-info">
                <strong>Referencia de Seguimiento:</strong> {attempt_number}<br>
                <strong>ID de Lead:</strong> #{lead_id}
            </div>

            <p>Nuestros robots no solo optimizan tareas; generan un impacto visual y operativo que <span class="highlight">dispara la rentabilidad</span> de tu negocio.</p>

            <ul class="benefits">
                <li>Atención al cliente de alto nivel.</li>
                <li>Reducción real en costos operativos.</li>
                <li>Implementación especializada y soporte local.</li>
            </ul>

            <div class="cta-container">
                <a href="https://wa.me/message/LLZ2X6D44CXYJ1" class="btn-whatsapp">HABLAR POR WHATSAPP AHORA</a>
                <p class="reply-text">O si lo prefieres, <strong>responde directamente a este correo</strong> y un asesor se pondrá en contacto contigo.</p>
            </div>
        </div>

        <div class="footer">
            <p><strong>Servibot México</strong><br>Tecnología que mueve tu mundo.</p>
            <p><a href="https://www.servibot.mx" style="color: #0052cc; text-decoration: none;">www.servibot.mx</a></p>
        </div>
    </div>
</body>
</html>
"""

            # Enviar HTML en el campo `body` para compatibilidad con la Lambda
            response = requests.post(
                self.lambda_email_url,
                json={
                    "function": "enviar_email_aws",
                    "params": {
                        "to": email,
                        "subject": f"Aviso de Pegasus Control - Seguimiento {attempt_number}",
                        "body": body_html,
                    },
                },
                headers={"Content-Type": "application/json"},
                timeout=15,
            )
            response.raise_for_status()

            return {
                "lead_id": lead_id,
                "status": "success",
                "message": f"Email enviado a {email}",
            }
        except Exception as e:
            return {
                "lead_id": lead_id,
                "status": "error",
                "message": f"Error enviando email: {str(e)}",
            }

    def register_lead_attempt(
        self, lead_id: int, email: str, attempt_number: int
    ) -> Dict[str, Any]:
        """
        Registra un intento de email en Odoo vía Lambda.

        Args:
            lead_id: ID del lead
            email: Email al que se envió
            attempt_number: Número de intento (1, 2 o 3)

        Returns:
            {
                "success": bool,
                "attempt_number": int,
                "should_stop": bool
            }
        """
        try:
            response = requests.post(
                self.lambda_odoo_url,
                json={
                    "function": "add_lead_attempt",
                    "params": {
                        "lead_id": lead_id,
                        "max_attempts": 3,
                        "message_template": f"""📧 Intento {{attempt}} - Email enviado a {email} el {{date}}. Contenido del recordatorio:       Hola ,

Seguimos impulsando la innovación en México y queremos que seas parte de ello. Vimos tu interés en nuestras soluciones de robótica inteligente y no queremos que pierdas la oportunidad de transformar tu operación.

Referencia de Seguimiento: {{attempt}} . ID de Lead: #{{lead_id}}.

Nuestros robots no solo optimizan tareas; generan un impacto visual y operativo que dispara la rentabilidad de tu negocio. Ofrecen atención al cliente de alto nivel, una reducción real en costos operativos y una implementación especializada con soporte local.

Habla por WhatsApp ahora o, si lo prefieres, responde directamente a este correo y un asesor se pondrá en contacto contigo.

Servibot México. Tecnología que mueve tu mundo. www.servibot.mx
                        """,
                        "is_internal": True,
                    },
                },
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            return {
                "success": True,
                "attempt_number": data.get("attempt_number", attempt_number),
                "should_stop": data.get("should_stop", False),
            }
        except Exception as e:
            print(f"⚠️  Error registrando intento para lead {lead_id}: {e}")
            return {
                "success": False,
                "attempt_number": attempt_number,
                "should_stop": False,
            }

    def create_email_job(
        self,
        environment: str = "dev",
        lead_ids: Optional[List[int]] = None,
        domain: Optional[List] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Crea un job de email masivo y lo procesa en background.

        PRIORIDAD DE BÚSQUEDA:
        1. lead_ids → IDs específicos
        2. domain → Domain de Odoo
        3. filters → Filtros simples
        4. default → IDs fijos de testing

        Args:
            environment: DEPRECADO - Mantener por compatibilidad
            lead_ids: Lista de IDs específicos a procesar
            domain: Domain de Odoo para búsqueda avanzada
            filters: Filtros simples (days_ago, max_messages, etc.)
            filters: Filtros adicionales (opcional)

        Returns:
            job_id del job creado
        """
        job_id = str(uuid.uuid4())[:8]

        # Obtener leads según prioridad
        leads = self.get_leads(
            environment=environment, lead_ids=lead_ids, domain=domain, filters=filters
        )

        if not leads:
            raise ValueError("No se encontraron leads para procesar")

        # Crear registro del job
        job_info = {
            "job_id": job_id,
            "status": "queued",
            "environment": environment,
            "lead_ids": lead_ids,
            "domain": domain,
            "filters": filters,
            "total_leads": len(leads),
            "processed": 0,
            "successes": 0,
            "failures": 0,
            "skipped": 0,
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
        }

        with self.jobs_lock:
            self.jobs[job_id] = job_info

        # Log inicial
        email_logger.log_job_start(
            job_id=job_id,
            filters=filters or {},
            total_leads=len(leads),
            batch_size=self.batch_size,
            environment=environment,
        )

        # Procesar en background
        thread = threading.Thread(
            target=self._execute_job,
            args=(job_id, leads),
            daemon=True,
        )
        thread.start()

        print(f"🚀 Email job {job_id} iniciado ({len(leads)} leads)")

        return job_id

    def _execute_job(self, job_id: str, leads: List[Dict[str, Any]]):
        """
        Ejecuta el job de email masivo (llamado en thread).

        Args:
            job_id: ID del job
            leads: Lista de leads a procesar
        """
        start_time = time.time()

        with self.jobs_lock:
            self.jobs[job_id]["status"] = "processing"

        try:
            # Dividir en batches
            batches = [
                leads[i : i + self.batch_size]
                for i in range(0, len(leads), self.batch_size)
            ]

            for batch_number, batch in enumerate(batches, start=1):
                batch_results = self._process_batch(batch_number, batch)

                # Actualizar contadores
                with self.jobs_lock:
                    job = self.jobs[job_id]
                    job["processed"] += len(batch)
                    job["successes"] += sum(
                        1 for r in batch_results if r["status"] == "success"
                    )
                    job["failures"] += sum(
                        1 for r in batch_results if r["status"] == "error"
                    )
                    job["skipped"] += sum(
                        1 for r in batch_results if r["status"] == "skipped"
                    )

                # Loguear batch
                email_logger.log_batch(job_id, batch_number, batch_results)

                # Delay entre batches (excepto el último)
                if batch_number < len(batches):
                    time.sleep(self.batch_delay)

            # Finalizar job
            duration = time.time() - start_time

            with self.jobs_lock:
                job = self.jobs[job_id]
                job["status"] = "completed"
                job["completed_at"] = datetime.now().isoformat()

            email_logger.log_job_complete(
                job_id=job_id,
                total_leads=job["total_leads"],
                total_successes=job["successes"],
                total_failures=job["failures"],
                total_skipped=job["skipped"],
                duration_seconds=duration,
            )

            print(f"✅ Job {job_id} completado en {duration:.2f}s")

        except Exception as e:
            with self.jobs_lock:
                self.jobs[job_id]["status"] = "failed"
                self.jobs[job_id]["error"] = str(e)

            email_logger.log_job_error(job_id, str(e))
            print(f"❌ Job {job_id} falló: {e}")

    def _process_batch(
        self, batch_number: int, batch: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Procesa un batch de leads.

        Args:
            batch_number: Número del batch
            batch: Lista de leads del batch

        Returns:
            Lista de resultados por lead
        """
        results = []

        print(f"🔄 Procesando batch {batch_number} ({len(batch)} leads)...")

        for lead in batch:
            lead_id = lead["id"]
            email = lead.get("email_from") or (
                lead.get("partner_id", [None, None])[1]
                if lead.get("partner_id")
                else None
            )

            # 1. Verificar intentos
            attempt_check = self.check_lead_attempts(lead_id)

            if not attempt_check["can_send"]:
                results.append(
                    {
                        "lead_id": lead_id,
                        "status": "skipped",
                        "reason": f"Máximo de intentos alcanzado ({attempt_check['attempts']}/3)",
                        "attempts": attempt_check["attempts"],
                    }
                )
                continue

            # 2. Calcular siguiente número de intento
            next_attempt = attempt_check["attempts"] + 1

            # 3. Enviar email
            send_result = self.send_email_to_lead(lead, next_attempt)

            if send_result["status"] == "error":
                results.append(
                    {
                        "lead_id": lead_id,
                        "status": "error",
                        "message": send_result["message"],
                        "attempts_before": attempt_check["attempts"],
                    }
                )
                continue

            # 4. Registrar intento en Odoo
            register_result = self.register_lead_attempt(
                lead_id, email or "sin_email", next_attempt
            )

            results.append(
                {
                    "lead_id": lead_id,
                    "status": "success",
                    "message": send_result["message"],
                    "attempts_before": attempt_check["attempts"],
                    "current_attempt": register_result["attempt_number"],
                    "should_stop": register_result["should_stop"],
                    "registered_in_odoo": register_result["success"],
                }
            )

        return results

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el estado actual de un job.

        Args:
            job_id: ID del job

        Returns:
            Información del job o None si no existe
        """
        with self.jobs_lock:
            return self.jobs.get(job_id)
