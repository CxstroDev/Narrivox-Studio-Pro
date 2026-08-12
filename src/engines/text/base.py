import logging
from abc import ABC, abstractmethod
from src.interfaces import ITextGenerator

logger = logging.getLogger("Narrivox")

class TextProviderBase(ITextGenerator, ABC):
    """Clase base para proveedores de texto/IA."""
    def __init__(self, config: dict):
        self.config = config

    def cancel(self):
        pass

    def is_available(self) -> bool:
        return True

    def get_model_info(self) -> dict:
        return {"provider": self.__class__.__name__}
