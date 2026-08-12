# src/ollama_client.py
"""
Cliente para interactuar con Ollama (API local).
Permite listar modelos instalados y generar texto.
"""
import logging

import requests

logger = logging.getLogger("Narrivox")

class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api"

    def is_server_running(self) -> bool:
        """Verifica si el servidor de Ollama está activo."""
        try:
            response = requests.get(f"{self.base_url}/", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    def list_models(self) -> list[dict]:
        """Obtiene la lista de modelos instalados en Ollama."""
        if not self.is_server_running():
            logger.warning("Ollama no está en ejecución.")
            return []
        try:
            response = requests.get(f"{self.api_url}/tags", timeout=5)
            response.raise_for_status()
            data = response.json()
            models = []
            for model in data.get("models", []):
                models.append({
                    "id": model["name"],
                    "name": model["name"],
                    "size_gb": model.get("size", 0) / (1024**3),
                    "description": f"Modelo Ollama: {model.get('details', {}).get('family', '')}",
                    "source": "ollama"
                })
            return models
        except Exception as e:
            logger.error(f"Error listando modelos de Ollama: {e}")
            return []

    def generate(self, model: str, prompt: str, system_msg: str = "", stream: bool = False) -> str | None:
        """Genera texto usando un modelo de Ollama."""
        if not self.is_server_running():
            raise ConnectionError("Ollama no está disponible.")
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ],
            "stream": stream,
            "options": {"temperature": 0.7}
        }
        try:
            response = requests.post(f"{self.api_url}/chat", json=payload, timeout=60)
            response.raise_for_status()
            return response.json()["message"]["content"]
        except Exception as e:
            logger.error(f"Error generando con Ollama: {e}")
            raise
