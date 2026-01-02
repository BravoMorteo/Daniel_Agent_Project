"""
Helpers Module
==============
Funciones de utilidad compartidas para el servidor MCP-Odoo.
"""

import json
import time
from typing import Dict, Any, Callable, TypeVar
from functools import wraps
import xmlrpc.client

T = TypeVar("T")


def encode_content(obj: Any) -> Dict[str, Any]:
    """
    Envuelve un objeto en el formato de content array de MCP.

    Args:
        obj: Objeto a envolver (será serializado como JSON)

    Returns:
        Dict con estructura: {"content": [{"type": "text", "text": "..."}]}
    """
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(obj, ensure_ascii=False),
            }
        ]
    }


def odoo_form_url(model: str, rec_id: int, base_url: str = None) -> str:
    """
    Genera URL del formulario de Odoo para un registro.

    Args:
        model: Nombre del modelo Odoo (ej: "project.project")
        rec_id: ID del registro
        base_url: URL base de Odoo (si None, usa variable de entorno)

    Returns:
        URL del formulario
    """
    if not base_url:
        from .config import Config

        base_url = Config.ODOO_URL

    if not base_url:
        return f"odoo://{model}/{rec_id}"

    base_url = base_url.rstrip("/")
    return f"{base_url}/web#id={rec_id}&model={model}&view_type=form"


def wants_projects(query: str) -> bool:
    """
    Detecta si la query busca proyectos.

    Args:
        query: Texto de búsqueda

    Returns:
        True si la query menciona proyectos
    """
    ql = query.lower()
    return any(t in ql for t in ("proyecto", "proyectos", "project", "projects"))


def wants_tasks(query: str) -> bool:
    """
    Detecta si la query busca tareas.

    Args:
        query: Texto de búsqueda

    Returns:
        True si la query menciona tareas
    """
    ql = query.lower()
    return any(t in ql for t in ("tarea", "tareas", "task", "tasks"))


def is_retryable_error(error: Exception) -> bool:
    """
    Determina si un error es temporal y se puede reintentar.

    Args:
        error: Excepción a evaluar

    Returns:
        True si el error es temporal y se debe reintentar
    """
    error_str = str(error).lower()
    error_type = type(error).__name__

    # Errores de red/conexión que se pueden reintentar
    retryable_errors = [
        "request-sent",  # XML-RPC connection interrupted
        "connection reset",
        "connection refused",
        "connection timeout",
        "timed out",
        "network is unreachable",
        "temporary failure",
        "service unavailable",
        "gateway timeout",
        "connection aborted",
        "broken pipe",
    ]

    # Verificar si el mensaje de error contiene algún patrón retryable
    if any(pattern in error_str for pattern in retryable_errors):
        return True

    # Errores específicos de xmlrpc.client
    if isinstance(
        error,
        (
            xmlrpc.client.ProtocolError,
            ConnectionError,
            TimeoutError,
        ),
    ):
        return True

    return False


def retry_on_network_error(
    max_attempts: int = 3,
    base_delay: float = 2.0,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
):
    """
    Decorador que reintenta una función en caso de errores de red temporales.

    Args:
        max_attempts: Número máximo de intentos (default: 3)
        base_delay: Delay inicial en segundos (default: 2.0)
        max_delay: Delay máximo en segundos (default: 10.0)
        backoff_factor: Factor de incremento exponencial (default: 2.0)

    Returns:
        Decorador que maneja reintentos automáticos

    Example:
        @retry_on_network_error(max_attempts=3, base_delay=2.0)
        def risky_network_call():
            # código que puede fallar por problemas de red
            pass
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_error = None

            for attempt in range(1, max_attempts + 1):
                try:
                    # Intentar ejecutar la función
                    return func(*args, **kwargs)

                except Exception as e:
                    last_error = e

                    # Verificar si es un error retryable
                    if not is_retryable_error(e):
                        # Si no es retryable, lanzar inmediatamente
                        raise

                    # Si es el último intento, lanzar el error
                    if attempt >= max_attempts:
                        print(
                            f"❌ Todos los reintentos fallaron ({max_attempts} intentos)"
                        )
                        raise

                    # Calcular delay con backoff exponencial
                    delay = min(
                        base_delay * (backoff_factor ** (attempt - 1)), max_delay
                    )

                    # Log del reintento
                    print(f"⚠️  Error temporal detectado: {type(e).__name__}: {str(e)}")
                    print(
                        f"🔄 Reintentando ({attempt}/{max_attempts}) en {delay:.1f}s..."
                    )

                    # Esperar antes de reintentar
                    time.sleep(delay)

            # Nunca debería llegar aquí, pero por si acaso
            if last_error:
                raise last_error

        return wrapper

    return decorator
