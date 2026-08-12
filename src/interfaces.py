# src/interfaces.py
"""
Interfaces abstractas para componentes de Narrivox.
Define contratos claros para implementaciones concretas.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from typing import Any, Optional


class ITextGenerator(ABC):
    """Interfaz para generadores de texto."""

    @abstractmethod
    def generate(self, prompt: str, system_msg: str = "",
                callback: Optional[Callable[[str, bool, bool], None]] = None,
                **kwargs) -> None:
        """
        Genera texto a partir de un prompt.

        Args:
            prompt: Texto de entrada
            system_msg: Mensaje del sistema
            callback: Función de callback (resultado, éxito, cancelado)
            **kwargs: Parámetros adicionales
        """
        pass

    @abstractmethod
    def cancel(self) -> None:
        """Cancela la generación actual."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Verifica si el generador está disponible."""
        pass

    @abstractmethod
    def get_model_info(self) -> dict:
        """Obtiene información del modelo."""
        pass


class IImageGenerator(ABC):
    """Interfaz para generadores de imágenes."""

    @abstractmethod
    def generate(self, prompt: str, negative_prompt: str = "",
                callback: Optional[Callable[[bytes, bool, str], None]] = None,
                **kwargs) -> None:
        """
        Genera una imagen a partir de un prompt.

        Args:
            prompt: Descripción de la imagen
            negative_prompt: Prompt negativo
            callback: Función de callback (imagen_bytes, éxito, error)
            **kwargs: Parámetros adicionales
        """
        pass

    @abstractmethod
    def cancel(self) -> None:
        """Cancela la generación actual."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Verifica si el generador está disponible."""
        pass

    @abstractmethod
    def get_model_info(self) -> dict:
        """Obtiene información del modelo."""
        pass


class IAudioGenerator(ABC):
    """Interfaz para generadores de audio."""

    @abstractmethod
    def generate_audio(self, text: str, voice: str, output_path: str,
                      callback: Optional[Callable[[bool, str], None]] = None,
                      **kwargs) -> Optional[str]:
        """
        Genera audio a partir de texto.

        Args:
            text: Texto a sintetizar
            voice: Voz a utilizar
            output_path: Ruta de salida
            callback: Función de callback (éxito, mensaje)
            **kwargs: Parámetros adicionales

        Returns:
            Ruta del archivo generado o None
        """
        pass

    @abstractmethod
    def get_available_voices(self) -> list[dict]:
        """Obtiene lista de voces disponibles."""
        pass

    @abstractmethod
    def cancel(self) -> None:
        """Cancela la generación actual."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Verifica si el generador está disponible."""
        pass


class IVideoProcessor(ABC):
    """Interfaz para procesadores de video."""

    @abstractmethod
    def assemble_video(self, image_path: str, audio_path: str,
                      output_path: str, **kwargs) -> bool:
        """
        Ensambla un video desde imagen y audio.

        Args:
            image_path: Ruta de la imagen
            audio_path: Ruta del audio
            output_path: Ruta de salida
            **kwargs: Parámetros adicionales

        Returns:
            True si se generó exitosamente
        """
        pass

    @abstractmethod
    def apply_effect(self, input_path: str, output_path: str,
                    effect_type: str, **kwargs) -> bool:
        """
        Aplica un efecto a un video.

        Args:
            input_path: Ruta de entrada
            output_path: Ruta de salida
            effect_type: Tipo de efecto
            **kwargs: Parámetros del efecto

        Returns:
            True si se aplicó exitosamente
        """
        pass

    @abstractmethod
    def get_supported_formats(self) -> list[str]:
        """Obtiene formatos de video soportados."""
        pass


class IDataStorage(ABC):
    """Interfaz para almacenamiento de datos."""

    @abstractmethod
    def save_project(self, data: dict) -> bool:
        """Guarda un proyecto."""
        pass

    @abstractmethod
    def get_project(self, project_id: str) -> Optional[dict]:
        """Obtiene un proyecto por ID."""
        pass

    @abstractmethod
    def get_all_projects(self) -> list[dict]:
        """Obtiene todos los proyectos."""
        pass

    @abstractmethod
    def delete_project(self, project_id: str) -> bool:
        """Elimina un proyecto."""
        pass

    @abstractmethod
    def search_projects(self, query: str) -> list[dict]:
        """Busca proyectos."""
        pass


class IConfigManager(ABC):
    """Interfaz para gestión de configuración."""

    @abstractmethod
    def load_config(self) -> dict:
        """Carga la configuración."""
        pass

    @abstractmethod
    def save_config(self, config: dict) -> bool:
        """Guarda la configuración."""
        pass

    @abstractmethod
    def get_value(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor de configuración."""
        pass

    @abstractmethod
    def set_value(self, key: str, value: Any) -> bool:
        """Establece un valor de configuración."""
        pass

    @abstractmethod
    def reset_to_defaults(self) -> bool:
        """Restablece la configuración a valores por defecto."""
        pass


class IModelManager(ABC):
    """Interfaz para gestión de modelos."""

    @abstractmethod
    def download_model(self, model_id: str, category: str,
                     progress_callback: Optional[Callable[[float, str], None]] = None) -> bool:
        """Descarga un modelo."""
        pass

    @abstractmethod
    def delete_model(self, model_id: str, category: str) -> bool:
        """Elimina un modelo."""
        pass

    @abstractmethod
    def get_installed_models(self, category: str) -> list[dict]:
        """Obtiene modelos instalados."""
        pass

    @abstractmethod
    def get_available_models(self, category: str) -> list[dict]:
        """Obtiene modelos disponibles."""
        pass

    @abstractmethod
    def set_active_model(self, model_id: str, category: str) -> bool:
        """Establece el modelo activo."""
        pass

    @abstractmethod
    def get_active_model(self, category: str) -> Optional[str]:
        """Obtiene el modelo activo."""
        pass


class ITaskQueue(ABC):
    """Interfaz para cola de tareas."""

    @abstractmethod
    def enqueue(self, task: dict, priority: int = 0) -> str:
        """Añade una tarea a la cola."""
        pass

    @abstractmethod
    def dequeue(self) -> Optional[dict]:
        """Obtiene la siguiente tarea."""
        pass

    @abstractmethod
    def cancel_task(self, task_id: str) -> bool:
        """Cancela una tarea."""
        pass

    @abstractmethod
    def get_task_status(self, task_id: str) -> Optional[str]:
        """Obtiene el estado de una tarea."""
        pass

    @abstractmethod
    def get_queue_size(self) -> int:
        """Obtiene el tamaño de la cola."""
        pass


class ICache(ABC):
    """Interfaz para sistema de caché."""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor del caché."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Almacena un valor en el caché."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Elimina un valor del caché."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Limpia todo el caché."""
        pass

    @abstractmethod
    def get_stats(self) -> dict:
        """Obtiene estadísticas del caché."""
        pass


class IValidator(ABC):
    """Interfaz para validación de datos."""

    @abstractmethod
    def validate(self, value: Any, field_name: str = "valor") -> tuple[bool, Optional[str]]:
        """
        Valida un valor.

        Args:
            value: Valor a validar
            field_name: Nombre del campo

        Returns:
            (es_válido, mensaje_error)
        """
        pass

    @abstractmethod
    def sanitize(self, value: Any) -> Any:
        """Sanitiza un valor."""
        pass


class ILogger(ABC):
    """Interfaz para sistema de logging."""

    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """Log de nivel debug."""
        pass

    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """Log de nivel info."""
        pass

    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """Log de nivel warning."""
        pass

    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        """Log de nivel error."""
        pass

    @abstractmethod
    def critical(self, message: str, **kwargs) -> None:
        """Log de nivel critical."""
        pass


class IProgressTracker(ABC):
    """Interfaz para seguimiento de progreso."""

    @abstractmethod
    def start(self, total_steps: int, description: str = "") -> None:
        """Inicia el seguimiento."""
        pass

    @abstractmethod
    def update(self, progress: float, message: str = "") -> None:
        """Actualiza el progreso."""
        pass

    @abstractmethod
    def complete(self, message: str = "") -> None:
        """Marca como completado."""
        pass

    @abstractmethod
    def fail(self, error_message: str) -> None:
        """Marca como fallido."""
        pass

    @abstractmethod
    def get_progress(self) -> float:
        """Obtiene el progreso actual."""
        pass


class IEventHandler(ABC):
    """Interfaz para manejo de eventos."""

    @abstractmethod
    def subscribe(self, event_type: str, handler: Callable) -> str:
        """Suscribe un handler a un evento."""
        pass

    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> bool:
        """Desuscribe un handler."""
        pass

    @abstractmethod
    def emit(self, event_type: str, data: Any = None) -> None:
        """Emite un evento."""
        pass

    @abstractmethod
    def get_event_types(self) -> list[str]:
        """Obtiene tipos de eventos disponibles."""
        pass


class IResourceMonitor(ABC):
    """Interfaz para monitoreo de recursos."""

    @abstractmethod
    def get_memory_usage(self) -> dict:
        """Obtiene uso de memoria."""
        pass

    @abstractmethod
    def get_cpu_usage(self) -> float:
        """Obtiene uso de CPU."""
        pass

    @abstractmethod
    def get_disk_usage(self, path: str) -> dict:
        """Obtiene uso de disco."""
        pass

    @abstractmethod
    def is_resource_available(self, resource_type: str, required: float) -> bool:
        """Verifica disponibilidad de recursos."""
        pass


class IRetryPolicy(ABC):
    """Interfaz para políticas de reintentos."""

    @abstractmethod
    def should_retry(self, attempt: int, error: Exception) -> bool:
        """Determina si se debe reintentar."""
        pass

    @abstractmethod
    def get_delay(self, attempt: int) -> float:
        """Obtiene el delay antes del siguiente intento."""
        pass

    @abstractmethod
    def get_max_attempts(self) -> int:
        """Obtiene el máximo número de intentos."""
        pass


class IService(ABC):
    """Interfaz base para servicios."""

    @abstractmethod
    def initialize(self) -> bool:
        """Inicializa el servicio."""
        pass

    @abstractmethod
    def shutdown(self) -> bool:
        """Apaga el servicio."""
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """Verifica si el servicio está corriendo."""
        pass

    @abstractmethod
    def get_status(self) -> dict:
        """Obtiene el estado del servicio."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verifica salud del servicio."""
        pass