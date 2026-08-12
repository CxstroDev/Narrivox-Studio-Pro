# src/hybrid_router.py
import logging

import requests

from src.model_utils import is_local_model_available

logger = logging.getLogger("Narrivox")

class HybridRouter:
    @staticmethod
    def has_internet() -> bool:
        try:
            requests.get("https://www.google.com", timeout=3)
            return True
        except requests.RequestException:
            return False

    @staticmethod
    def should_use_local(category: str, config: dict) -> bool:
        local_config = config.get("local_providers", {}).get(category, {})
        local_enabled = local_config.get("enabled", False)
        if not local_enabled:
            return False
        if not is_local_model_available(category, config):
            return False
        if not HybridRouter.has_internet():
            logger.info(f"Sin conexión. Usando {category} local.")
            return True
        if config.get("prefer_local", False):
            logger.info(f"Preferencia local activada. Usando {category} local.")
            return True
        return False
