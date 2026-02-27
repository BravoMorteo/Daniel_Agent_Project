"""
Logger especializado para email masivo (outbound emails).
Logs organizados en S3: outbound_mails/YYYY/MM/DD/
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import boto3
from botocore.exceptions import ClientError


class EmailLogger:
    """Gestiona el logging de emails masivos y subida a S3"""

    def __init__(
        self,
        log_dir: str = "/tmp/outbound_mails_logs",
        bucket_name: Optional[str] = None,
        aws_region: str = "us-east-1",
    ):
        """
        Inicializa el logger de emails.

        Args:
            log_dir: Directorio local para logs
            bucket_name: Nombre del bucket S3
            aws_region: Región de AWS
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.bucket_name = bucket_name
        self.aws_region = aws_region
        self.s3_client = None
        self.s3_enabled = False

        # Inicializar cliente S3 si está configurado
        if self.bucket_name:
            try:
                self.s3_client = boto3.client("s3", region_name=self.aws_region)
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                self.s3_enabled = True
                print(f"✅ Email Logger S3 inicializado correctamente")
            except Exception as e:
                print(f"⚠️  Email Logger S3 deshabilitado: {e}")
                self.s3_enabled = False

    def log_job_start(
        self,
        job_id: str,
        filters: Dict[str, Any],
        total_leads: int,
        batch_size: int,
        environment: str,
    ) -> str:
        """
        Registra el inicio de un job de email masivo.

        Args:
            job_id: ID único del job
            filters: Filtros aplicados para obtener leads
            total_leads: Número total de leads a procesar
            batch_size: Tamaño de cada batch
            environment: dev o prod

        Returns:
            Ruta del archivo de log
        """
        now = datetime.now()

        log_data = {
            "job_id": job_id,
            "created_at": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S.%f")[:-3],
            "status": "started",
            "environment": environment,
            "filters": filters,
            "total_leads": total_leads,
            "batch_size": batch_size,
            "total_batches": (total_leads + batch_size - 1) // batch_size,
            "estimated_duration_minutes": total_leads * 2 / 60,  # ~2 seg por email
        }

        # Guardar localmente
        log_filename = f"job_summary_{job_id}.json"
        log_path = self.log_dir / log_filename

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        print(f"📝 Email job iniciado: {log_path}")

        # Subir a S3 en carpeta outbound_mails/YYYY/MM/DD/
        if self.s3_enabled:
            self._upload_to_s3(log_path, log_filename, job_id)

        return str(log_path)

    def log_batch(
        self,
        job_id: str,
        batch_number: int,
        batch_results: List[Dict[str, Any]],
    ) -> str:
        """
        Registra los resultados de un batch.

        Args:
            job_id: ID del job
            batch_number: Número del batch
            batch_results: Lista de resultados por lead

        Returns:
            Ruta del archivo de log
        """
        now = datetime.now()

        successes = [r for r in batch_results if r.get("status") == "success"]
        failures = [r for r in batch_results if r.get("status") == "error"]
        skipped = [r for r in batch_results if r.get("status") == "skipped"]

        log_data = {
            "job_id": job_id,
            "batch_number": batch_number,
            "timestamp": now.isoformat(),
            "summary": {
                "total": len(batch_results),
                "successes": len(successes),
                "failures": len(failures),
                "skipped": len(skipped),
            },
            "results": batch_results,
        }

        # Guardar localmente
        log_filename = f"batch_{batch_number:03d}_{job_id}.json"
        log_path = self.log_dir / log_filename

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        print(
            f"📦 Batch {batch_number} completado: "
            f"{len(successes)} ✅ | {len(failures)} ❌ | {len(skipped)} ⏭️"
        )

        # Subir a S3
        if self.s3_enabled:
            self._upload_to_s3(log_path, log_filename, job_id)

        return str(log_path)

    def log_job_complete(
        self,
        job_id: str,
        total_leads: int,
        total_successes: int,
        total_failures: int,
        total_skipped: int,
        duration_seconds: float,
    ) -> str:
        """
        Registra la finalización de un job.

        Args:
            job_id: ID del job
            total_leads: Total de leads procesados
            total_successes: Total de emails enviados exitosamente
            total_failures: Total de fallos
            total_skipped: Total de leads omitidos
            duration_seconds: Duración total en segundos

        Returns:
            Ruta del archivo de log
        """
        now = datetime.now()

        log_data = {
            "job_id": job_id,
            "completed_at": now.isoformat(),
            "status": "completed",
            "summary": {
                "total_leads": total_leads,
                "successes": total_successes,
                "failures": total_failures,
                "skipped": total_skipped,
                "success_rate": (
                    round(total_successes / total_leads * 100, 2)
                    if total_leads > 0
                    else 0
                ),
            },
            "duration": {
                "seconds": round(duration_seconds, 2),
                "minutes": round(duration_seconds / 60, 2),
            },
        }

        # Guardar localmente
        log_filename = f"final_report_{job_id}.json"
        log_path = self.log_dir / log_filename

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Job completado: {log_path}")
        print(
            f"📊 Resumen: {total_successes}/{total_leads} exitosos "
            f"({log_data['summary']['success_rate']}%)"
        )

        # Subir a S3
        if self.s3_enabled:
            self._upload_to_s3(log_path, log_filename, job_id)

        return str(log_path)

    def log_job_error(self, job_id: str, error: str) -> str:
        """
        Registra un error crítico del job.

        Args:
            job_id: ID del job
            error: Mensaje de error

        Returns:
            Ruta del archivo de log
        """
        now = datetime.now()

        log_data = {
            "job_id": job_id,
            "failed_at": now.isoformat(),
            "status": "failed",
            "error": error,
        }

        # Guardar localmente
        log_filename = f"error_{job_id}.json"
        log_path = self.log_dir / log_filename

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        print(f"❌ Job falló: {log_path}")

        # Subir a S3
        if self.s3_enabled:
            self._upload_to_s3(log_path, log_filename, job_id)

        return str(log_path)

    def _upload_to_s3(self, local_path: Path, filename: str, job_id: str):
        """
        Sube un archivo de log a S3 en la carpeta outbound_mails/YYYY/MM/DD/job_id/

        Args:
            local_path: Ruta local del archivo
            filename: Nombre del archivo
            job_id: ID del job
        """
        if not self.s3_enabled:
            return

        try:
            # Estructura: outbound_mails/2026/02/26/job_abc123/batch_001.json
            now = datetime.now()
            year = now.strftime("%Y")
            month = now.strftime("%m")
            day = now.strftime("%d")

            s3_key = f"outbound_mails/{year}/{month}/{day}/{job_id}/{filename}"

            # Metadatos personalizados para tracking
            metadata = {
                "job-id": job_id,
                "upload-timestamp": now.isoformat(),
                "file-type": filename.split("_")[
                    0
                ],  # job_summary, batch, final_report, error
            }

            self.s3_client.upload_file(
                str(local_path),
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    "ContentType": "application/json",
                    "ServerSideEncryption": "AES256",
                    "Metadata": metadata,
                },
            )

            s3_url = f"s3://{self.bucket_name}/{s3_key}"
            print(f"☁️  Log subido a S3: {s3_url}")

        except Exception as e:
            print(f"⚠️  Error subiendo a S3: {e}")


# Instancia global del logger
_bucket_name = os.getenv("S3_LOGS_BUCKET")
_aws_region = os.getenv("AWS_REGION", "us-east-1")

email_logger = EmailLogger(
    log_dir="/tmp/outbound_mails_logs",
    bucket_name=_bucket_name,
    aws_region=_aws_region,
)
