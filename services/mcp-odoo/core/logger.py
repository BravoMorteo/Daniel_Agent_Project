"""
Logger para guardar flujos de entrada/salida en JSON y subirlos a S3.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError


class QuotationLogger:
    """Gestiona el logging de cotizaciones y subida a S3"""

    def __init__(
        self,
        log_dir: str = "/tmp/mcp_odoo_logs",
        bucket_name: Optional[str] = None,
        aws_region: str = "us-east-1",
    ):
        """
        Inicializa el logger.

        Args:
            log_dir: Directorio local para logs
            bucket_name: Nombre del bucket S3 (None = solo local)
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
                print(f"[S3] Inicializando cliente S3...")
                print(f"[S3] Bucket: {self.bucket_name}")
                print(f"[S3] Region: {self.aws_region}")

                # Crear cliente S3 (usará credenciales disponibles automáticamente)
                # En local: usa ~/.aws/credentials
                # En App Runner: usa Instance Role si está configurado
                self.s3_client = boto3.client("s3", region_name=self.aws_region)

                # Verificar credenciales intentando listar el bucket
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                self.s3_enabled = True
                print(f"✅ Cliente S3 inicializado correctamente")

            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "Unknown")
                print(f"❌ Error de credenciales S3 ({error_code}): {e}")
                print(f"   → Los logs se guardarán solo localmente en {log_dir}")
                self.s3_enabled = False
            except Exception as e:
                print(f"⚠️  No se pudo inicializar cliente S3: {e}")
                print(f"   → Los logs se guardarán solo localmente en {log_dir}")
                self.s3_enabled = False

    def log_quotation(
        self,
        tracking_id: str,
        input_data: Dict[str, Any],
        output_data: Optional[Dict[str, Any]] = None,
        status: str = "started",
        error: Optional[str] = None,
    ) -> str:
        """
        Registra una cotización en formato JSON.

        Args:
            tracking_id: ID de seguimiento
            input_data: Datos de entrada
            output_data: Datos de salida (None si aún no hay)
            status: Estado (started, processing, completed, failed)
            error: Mensaje de error si falló

        Returns:
            Ruta del archivo de log
        """
        timestamp = datetime.now()
        log_entry = {
            "tracking_id": tracking_id,
            "timestamp": timestamp.isoformat(),
            "date": timestamp.strftime("%Y-%m-%d"),
            "time": timestamp.strftime("%H:%M:%S.%f")[:-3],
            "status": status,
            "input": input_data,
            "output": output_data,
            "error": error,
        }

        # Generar nombre de archivo: YYYY-MM-DD_tracking_id.log
        date_str = timestamp.strftime("%Y-%m-%d")
        log_filename = f"{date_str}_{tracking_id}.log"
        log_path = self.log_dir / log_filename

        # Escribir log en archivo
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)

        print(f"📝 Log guardado localmente: {log_path}")

        # Subir a S3 si está habilitado
        if self.s3_enabled:
            self._upload_to_s3(log_path, log_filename)

        return str(log_path)

    def update_quotation_log(
        self,
        tracking_id: str,
        output_data: Dict[str, Any],
        status: str = "completed",
        error: Optional[str] = None,
    ):
        """
        Actualiza un log existente con el resultado final.

        Args:
            tracking_id: ID de seguimiento
            output_data: Datos de salida
            status: Estado final (completed, failed)
            error: Mensaje de error si falló
        """
        # Buscar el archivo de log
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_filename = f"{date_str}_{tracking_id}.log"
        log_path = self.log_dir / log_filename

        if not log_path.exists():
            print(f"⚠️  Log no encontrado: {log_path}")
            return

        # Leer log existente
        with open(log_path, "r", encoding="utf-8") as f:
            log_entry = json.load(f)

        # Actualizar con output
        log_entry["output"] = output_data
        log_entry["status"] = status
        log_entry["error"] = error
        log_entry["updated_at"] = datetime.now().isoformat()

        # Guardar actualización
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)

        print(f"📝 Log actualizado: {log_path}")

        # Subir versión actualizada a S3
        if self.s3_enabled:
            self._upload_to_s3(log_path, log_filename)

    def _upload_to_s3(self, local_path: Path, s3_key: str):
        """
        Sube un archivo de log a S3.

        Args:
            local_path: Ruta local del archivo
            s3_key: Key del objeto en S3 (ruta en el bucket)
        """
        if not self.s3_enabled:
            print(f"⚠️  S3 deshabilitado, log solo guardado localmente")
            return

        try:
            # Agregar prefijo con año/mes para organización
            date_prefix = datetime.now().strftime("%Y/%m")
            full_s3_key = f"mcp-odoo-logs/{date_prefix}/{s3_key}"

            print(f"[S3] Subiendo log a S3...")
            print(f"[S3] Bucket: {self.bucket_name}")
            print(f"[S3] Key: {full_s3_key}")

            self.s3_client.upload_file(
                str(local_path),
                self.bucket_name,
                full_s3_key,
                ExtraArgs={
                    "ContentType": "application/json",
                    "ServerSideEncryption": "AES256",
                },
            )

            s3_url = f"s3://{self.bucket_name}/{full_s3_key}"
            print(f"☁️  ✅ Log subido exitosamente a S3: {s3_url}")

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_msg = e.response.get("Error", {}).get("Message", str(e))
            print(f"❌ Error de S3 ({error_code}): {error_msg}")
            print(f"   → Bucket: {self.bucket_name}")
            print(f"   → Key: {full_s3_key}")
            print(f"   → El log permanece guardado localmente en: {local_path}")
        except Exception as e:
            print(f"❌ Error inesperado subiendo a S3: {type(e).__name__}: {e}")
            print(f"   → El log permanece guardado localmente en: {local_path}")

    def get_log_path(self, tracking_id: str) -> Optional[Path]:
        """
        Obtiene la ruta del archivo de log para un tracking_id.

        Args:
            tracking_id: ID de seguimiento

        Returns:
            Path del archivo o None si no existe
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_filename = f"{date_str}_{tracking_id}.log"
        log_path = self.log_dir / log_filename

        return log_path if log_path.exists() else None

    def cleanup_old_logs(self, days: int = 7):
        """
        Elimina logs locales más antiguos que N días.
        Los logs en S3 no se eliminan (usar lifecycle policy del bucket).

        Args:
            days: Días de retención local
        """
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days)

        deleted_count = 0
        for log_file in self.log_dir.glob("*.log"):
            try:
                # Extraer fecha del nombre de archivo (YYYY-MM-DD_...)
                date_str = log_file.stem.split("_")[0]
                file_date = datetime.strptime(date_str, "%Y-%m-%d")

                if file_date < cutoff_date:
                    log_file.unlink()
                    deleted_count += 1
            except Exception as e:
                print(f"⚠️  Error procesando {log_file}: {e}")

        if deleted_count > 0:
            print(f"🗑️  Eliminados {deleted_count} logs antiguos")


# Instancia global del logger
# Configurar con variables de entorno
_bucket_name = os.getenv("S3_LOGS_BUCKET")
_aws_region = os.getenv("AWS_REGION", "us-east-1")
_log_dir = os.getenv("MCP_LOG_DIR", "/tmp/mcp_odoo_logs")

quotation_logger = QuotationLogger(
    log_dir=_log_dir, bucket_name=_bucket_name, aws_region=_aws_region
)
