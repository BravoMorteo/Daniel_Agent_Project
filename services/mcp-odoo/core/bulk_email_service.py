"""
Servicio para envío masivo de emails a leads.
Procesamiento por batches con threading no-bloqueante.
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
        """Inicializa el servicio de email masivo"""
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

        print(f"✅ BulkEmailService inicializado (batch_size={self.batch_size})")

    def get_leads(
        self,
        environment: str = "dev",
        lead_ids: Optional[List[int]] = None,
        domain: Optional[List] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Obtiene leads según la estrategia de búsqueda.

        PRIORIDAD DE BÚSQUEDA:
        1. lead_ids → Busca por IDs específicos (ignora todo lo demás)
        2. filters → Construye domain automáticamente desde filtros
        3. domain → Usa domain de Odoo directamente
        4. default → Filtro por defecto (últimos 60 días, ≤2 mensajes)

        NOTA: El parámetro 'environment' es legacy y será deprecado.
        La conexión a Odoo DEV/PROD se controla con ODOO_ENVIRONMENT.

        Args:
            environment: DEPRECADO - Mantener por compatibilidad
            lead_ids: Lista de IDs específicos a buscar
            domain: Domain de Odoo para búsqueda avanzada
            filters: Filtros simples (days_ago, max_messages, etc.)

        Returns:
            Lista de leads con id, name, partner_id, user_id, email_from, phone

        Ejemplos:
            # IDs específicos
            get_leads(lead_ids=[31697, 31698])

            # Filtros personalizados
            get_leads(filters={"days_ago": 30, "max_messages": 5})

            # Domain de Odoo
            get_leads(domain=[["create_date", ">=", "2026-01-01"]])

            # Default (filtro: 60 días, ≤2 mensajes)
            get_leads()
        """
        # PRIORIDAD 1: IDs específicos
        if lead_ids:
            final_domain = [["id", "in", lead_ids]]
            search_type = f"IDs específicos ({len(lead_ids)} leads)"

        # PRIORIDAD 2: Filtros simples (o default si no hay nada)
        else:
            # Si no se pasan filtros, usar filtros por defecto
            if not filters:
                # Filtro default: leads creados después de fecha específica
                final_domain = [["create_date", ">", "2026-02-25 23:24:05"]]
                search_type = "filtro default (create_date > 2026-02-25 23:24:05)"
            else:
                final_domain = []

                # Filtro: días atrás
                if "days_ago" in filters:
                    days_ago = (
                        datetime.now() - timedelta(days=filters["days_ago"])
                    ).strftime("%Y-%m-%d")
                    final_domain.append(["create_date", ">=", days_ago])

                # Filtro: máximo de mensajes (DESHABILITADO - campo no existe en Odoo)
                # if "max_messages" in filters:
                #     final_domain.append(["message_count", "<=", filters["max_messages"]])

                # Filtro: stage_id
                if "stage_id" in filters:
                    final_domain.append(["stage_id", "=", filters["stage_id"]])

                # Filtro: user_id
                if "user_id" in filters:
                    final_domain.append(["user_id", "=", filters["user_id"]])

                search_type = f"filtros ({len(final_domain)} condiciones)"

        fields = ["id", "name", "partner_id", "user_id", "email_from", "phone"]

        try:
            leads = self.odoo_client.search_read("crm.lead", final_domain, fields)
            odoo_env = os.getenv("ODOO_ENVIRONMENT", "dev")
            print(
                f"📋 Obtenidos {len(leads)} leads (Odoo: {odoo_env}, búsqueda: {search_type})"
            )
            return leads
        except Exception as e:
            print(f"❌ Error obteniendo leads: {e}")
            return []

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
            body_html = f"""Hola {name},

Espero te encuentres bien.
Vimos que te interesaste por nuestros servicios de Servibot y quería saber si aún necesitas ayuda o asesoramiento.

Esta información corresponde a tu solicitud de {name} registrada con el ID de lead {lead_id}.

En caso de que sigas interesado, con gusto te ayudaremos en lo que necesites.

Saludos,
Equipo Pegasus Control
"""

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
                        "message_template": f"📧 Intento {{attempt}} - Email enviado a {email} el {{date}}",
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
