import logging
from abc import ABC, abstractmethod
from src.interfaces import IImageGenerator

logger = logging.getLogger("Narrivox")

class ImageProviderBase(IImageGenerator, ABC):
    """Clase base para proveedores de imágenes."""
    def __init__(self, config: dict):
        self.config = config

    def cancel(self):
        """Implementación por defecto de cancelación (opcional)."""
        pass

    def is_available(self) -> bool:
        """Por defecto disponible, las subclases pueden sobrescribir."""
        return True

    def get_model_info(self) -> dict:
        return {"provider": self.__class__.__name__}
