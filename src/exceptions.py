# src/exceptions.py
# Excepciones personalizadas para Narrivox

from typing import Any, Optional


class NarrivoxError(Exception):
    """Excepción base del proyecto."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self):
        if self.details:
            return f"{self.message} - Detalles: {self.details}"
        return self.message


class DatabaseError(NarrivoxError):
    """Error relacionado con la base de datos."""

    def __init__(self, message: str, operation: Optional[str] = None, table: Optional[str] = None):
        details = {}
        if operation:
            details['operation'] = operation
        if table:
            details['table'] = table
        super().__init__(message, details)


class APIKeyMissingError(NarrivoxError):
    """Falta la API Key de un servicio."""

    def __init__(self, service: str, message: str = "API Key no configurada"):
        super().__init__(f"{service}: {message}", {'service': service})


class AudioGenerationError(NarrivoxError):
    """Error al generar audio."""

    def __init__(self, message: str, provider: Optional[str] = None,
                 voice: Optional[str] = None, text_length: Optional[int] = None):
        details = {}
        if provider:
            details['provider'] = provider
        if voice:
            details['voice'] = voice
        if text_length is not None:
            details['text_length'] = text_length
        super().__init__(message, details)


class ImageGenerationError(NarrivoxError):
    """Error al generar imagen."""

    def __init__(self, message: str, provider: Optional[str] = None,
                 prompt_length: Optional[int] = None, dimensions: Optional[tuple] = None):
        details = {}
        if provider:
            details['provider'] = provider
        if prompt_length is not None:
            details['prompt_length'] = prompt_length
        if dimensions:
            details['dimensions'] = dimensions
        super().__init__(message, details)


class ModelLoadError(NarrivoxError):
    """Error al cargar un modelo local."""

    def __init__(self, message: str, model_id: Optional[str] = None,
                 model_type: Optional[str] = None, memory_required: Optional[int] = None):
        details = {}
        if model_id:
            details['model_id'] = model_id
        if model_type:
            details['model_type'] = model_type
        if memory_required:
            details['memory_required_mb'] = memory_required
        super().__init__(message, details)


class ValidationError(NarrivoxError):
    """Error de validación de datos."""

    def __init__(self, message: str, field: Optional[str] = None,
                 value: Optional[Any] = None, constraint: Optional[str] = None):
        details = {}
        if field:
            details['field'] = field
        if value is not None:
            details['value'] = str(value)[:100]  # Limitar longitud
        if constraint:
            details['constraint'] = constraint
        super().__init__(message, details)


class ConfigurationError(NarrivoxError):
    """Error en la configuración."""

    def __init__(self, message: str, config_key: Optional[str] = None,
                 config_file: Optional[str] = None):
        details = {}
        if config_key:
            details['config_key'] = config_key
        if config_file:
            details['config_file'] = config_file
        super().__init__(message, details)


class NetworkError(NarrivoxError):
    """Error de conexión o red."""

    def __init__(self, message: str, url: Optional[str] = None,
                 status_code: Optional[int] = None, timeout: Optional[float] = None):
        details = {}
        if url:
            details['url'] = url
        if status_code:
            details['status_code'] = status_code
        if timeout:
            details['timeout'] = timeout
        super().__init__(message, details)


class ResourceExhaustedError(NarrivoxError):
    """Error por agotamiento de recursos."""

    def __init__(self, message: str, resource_type: Optional[str] = None,
                 available: Optional[float] = None, required: Optional[float] = None):
        details = {}
        if resource_type:
            details['resource_type'] = resource_type
        if available is not None:
            details['available'] = available
        if required is not None:
            details['required'] = required
        super().__init__(message, details)


class TaskTimeoutError(NarrivoxError):
    """Error por timeout de una tarea."""

    def __init__(self, message: str, task_id: Optional[str] = None,
                 timeout: Optional[float] = None, elapsed: Optional[float] = None):
        details = {}
        if task_id:
            details['task_id'] = task_id
        if timeout:
            details['timeout'] = timeout
        if elapsed:
            details['elapsed'] = elapsed
        super().__init__(message, details)


class TaskCancelledError(NarrivoxError):
    """Error por cancelación de una tarea."""

    def __init__(self, message: str = "Tarea cancelada por el usuario",
                 task_id: Optional[str] = None):
        details = {}
        if task_id:
            details['task_id'] = task_id
        super().__init__(message, details)
