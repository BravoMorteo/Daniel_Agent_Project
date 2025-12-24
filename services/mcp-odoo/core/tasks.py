"""
Gestión de tareas asíncronas para cotizaciones.
Almacena el estado de las tareas en memoria.
"""

from datetime import datetime
from typing import Dict, Optional, Any
from enum import Enum


class TaskStatus(str, Enum):
    """Estados posibles de una tarea"""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class QuotationTask:
    """Representa una tarea de cotización en proceso"""

    def __init__(self, task_id: str, params: dict):
        self.id = task_id
        self.status = TaskStatus.QUEUED
        self.params = params
        self.result: Optional[Any] = None
        self.error: Optional[str] = None
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.progress: Optional[str] = None

    def start(self):
        """Marca la tarea como en proceso"""
        self.status = TaskStatus.PROCESSING
        self.started_at = datetime.now()

    def complete(self, result: Any):
        """Marca la tarea como completada"""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.now()

    def fail(self, error: str):
        """Marca la tarea como fallida"""
        self.status = TaskStatus.FAILED
        self.error = error
        self.completed_at = datetime.now()

    def update_progress(self, message: str):
        """Actualiza el mensaje de progreso"""
        self.progress = message

    def elapsed_seconds(self) -> float:
        """Tiempo transcurrido desde la creación"""
        end_time = self.completed_at if self.completed_at else datetime.now()
        return (end_time - self.created_at).total_seconds()

    def to_dict(self) -> dict:
        """Convierte la tarea a diccionario para respuesta JSON"""
        data = {
            "tracking_id": self.id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "elapsed_time": f"{self.elapsed_seconds():.2f}s",
        }

        if self.progress:
            data["progress"] = self.progress

        if self.started_at:
            data["started_at"] = self.started_at.isoformat()

        if self.status == TaskStatus.COMPLETED and self.result:
            data["result"] = self.result
            data["completed_at"] = self.completed_at.isoformat()

        elif self.status == TaskStatus.FAILED and self.error:
            data["error"] = self.error
            data["completed_at"] = self.completed_at.isoformat()

        return data


class TaskManager:
    """Gestor de tareas en memoria"""

    def __init__(self):
        self._tasks: Dict[str, QuotationTask] = {}

    def create_task(self, task_id: str, params: dict) -> QuotationTask:
        """Crea una nueva tarea"""
        task = QuotationTask(task_id, params)
        self._tasks[task_id] = task
        return task

    def get_task(self, task_id: str) -> Optional[QuotationTask]:
        """Obtiene una tarea por ID"""
        return self._tasks.get(task_id)

    def task_exists(self, task_id: str) -> bool:
        """Verifica si una tarea existe"""
        return task_id in self._tasks

    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Limpia tareas antiguas (opcional, para evitar memory leak)"""
        now = datetime.now()
        to_remove = []

        for task_id, task in self._tasks.items():
            if task.completed_at:
                age_hours = (now - task.completed_at).total_seconds() / 3600
                if age_hours > max_age_hours:
                    to_remove.append(task_id)

        for task_id in to_remove:
            del self._tasks[task_id]

        return len(to_remove)


# Instancia global del gestor de tareas
task_manager = TaskManager()
