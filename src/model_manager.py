# src/model_manager.py
"""
Gestor central de modelos locales para Narrivox.
Maneja el escaneo, descarga, eliminación y selección de modelos para Texto, Imagen y TTS.
"""

import json
import logging
import shutil
import threading
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download

from src.model_utils import ensure_models_dir, get_model_path
from src.ollama_client import OllamaClient

logger = logging.getLogger("Narrivox")

# Categorías soportadas
CATEGORIES = ["text", "image", "tts"]

# Catálogo base de modelos recomendados (se puede ampliar desde JSON externo)
DEFAULT_CATALOG = {
    "text": [
        {
            "id": "Qwen/Qwen2.5-1.5B-Instruct",
            "name": "Qwen 2.5 1.5B Instruct",
            "size_gb": 3.0,
            "description": "Ligero y rápido, ideal para guiones en CPU.",
            "tags": ["recomendado", "cpu"]
        },
        {
            "id": "meta-llama/Llama-3.2-1B-Instruct",
            "name": "Llama 3.2 1B Instruct",
            "size_gb": 2.5,
            "description": "Excelente comprensión contextual, muy rápido.",
            "tags": ["popular", "cpu"]
        },
        {
            "id": "mistralai/Mistral-7B-Instruct-v0.3",
            "name": "Mistral 7B Instruct v0.3",
            "size_gb": 14.0,
            "description": "Muy creativo, calidad superior. Requiere más RAM.",
            "tags": ["avanzado", "cpu"]
        }
    ],
    "image": [
        {
            "id": "OFA-Sys/small-stable-diffusion-v0",
            "name": "Small Stable Diffusion v0",
            "size_gb": 2.0,
            "description": "Muy rápido, ideal para pruebas y prototipos.",
            "tags": ["recomendado", "cpu"]
        },
        {
            "id": "stabilityai/sdxl-turbo",
            "name": "SDXL Turbo",
            "size_gb": 7.0,
            "description": "Alta calidad en pocos pasos. Requiere 8+ GB RAM.",
            "tags": ["avanzado", "cpu"]
        },
        {
            "id": "black-forest-labs/FLUX.1-schnell",
            "name": "FLUX.1 Schnell",
            "size_gb": 12.0,
            "description": "Calidad fotorrealista superior. Pesado.",
            "tags": ["experimental", "cpu"]
        }
    ],
    "tts": [
        {
            "id": "hexgrad/Kokoro-82M",
            "name": "Kokoro 82M",
            "size_gb": 0.33,
            "description": "Voces naturales en varios idiomas. Requiere Docker.",
            "tags": ["recomendado", "docker"]
        }
    ]
}

class ModelManager:
    """Gestor de modelos locales para todas las categorías."""

    def __init__(self, config: dict):
        self.config = config
        self.base_dir = ensure_models_dir()
        self.api = HfApi()
        self._download_lock = threading.Lock()
        self._cancel_flags: dict[str, threading.Event] = {}
        self.catalog = self._load_catalog()

    # ------------------------------------------------------------------
    # Métodos de escaneo y estado
    # ------------------------------------------------------------------
    def _load_catalog(self) -> dict:
        """Carga el catálogo desde models_catalog.json o usa el por defecto."""
        catalog_path = Path(__file__).parent.parent / "models_catalog.json"
        if catalog_path.exists():
            try:
                with open(catalog_path, encoding="utf-8") as f:
                    loaded = json.load(f)
                    # Asegurar que tenga las tres categorías
                    for cat in CATEGORIES:
                        if cat not in loaded:
                            loaded[cat] = DEFAULT_CATALOG.get(cat, [])
                    return loaded
            except Exception as e:
                logger.error(f"Error cargando catálogo: {e}, usando por defecto.")
        return DEFAULT_CATALOG.copy()

    def _scan_ollama_models(self):
        from src.ollama_client import OllamaClient
        client = OllamaClient()
        if client.is_server_running():
            return client.list_models()
        return []

    def scan_installed_models(self, category: str | None = None) -> dict:
        """
        Escanea los modelos instalados en la carpeta models/ y actualiza la configuración.
        Retorna un diccionario con la información de modelos instalados por categoría.
        """
        categories_to_scan = [category] if category else CATEGORIES
        installed = {}
        for cat in categories_to_scan:
            installed[cat] = self._scan_category(cat)
        return installed

    def _scan_category(self, category: str) -> dict[str, dict]:
        """Escanea una categoría específica y actualiza la configuración."""
        cat_config = self.config.get("local_providers", {}).get(category, {})
        local_path = get_model_path(category, self.config)
        models = {}

        if not local_path or not local_path.exists():
            return models

        # Determinar si la carpeta local_path en sí misma es un modelo válido
        is_model_dir = self._is_valid_model_directory(local_path, category)

        if is_model_dir:
            # La carpeta base es el modelo (ej. models/small-sd-v0)
            model_id = cat_config.get("model_id") or self._guess_model_id(local_path, category)
            size_mb = self._get_directory_size_mb(local_path)
            models[model_id] = {
                "path": str(local_path),
                "display_name": self._get_display_name(model_id, category),
                "size_mb": size_mb,
                "installed_date": datetime.fromtimestamp(local_path.stat().st_ctime).isoformat(),
                "source": "huggingface"
            }
        else:
            # Buscar subcarpetas que puedan ser modelos independientes
            for item in local_path.iterdir():
                if item.is_dir() and self._is_valid_model_directory(item, category):
                    model_id = self._guess_model_id(item, category)
                    if model_id:
                        size_mb = self._get_directory_size_mb(item)
                        models[model_id] = {
                            "path": str(item),
                            "display_name": self._get_display_name(model_id, category),
                            "size_mb": size_mb,
                            "installed_date": datetime.fromtimestamp(item.stat().st_ctime).isoformat(),
                            "source": "huggingface"
                        }

        # --- Escaneo de modelos de Ollama (solo categoría texto) ---
        if category == "text":
            try:
                ollama = OllamaClient()
                if ollama.is_server_running():
                    ollama_models = ollama.list_models()
                    for om in ollama_models:
                        model_id = f"ollama:{om['id']}"
                        models[model_id] = {
                            "path": "",
                            "display_name": f"{om['name']} (Ollama)",
                            "size_mb": om.get("size_gb", 0) * 1024,
                            "installed_date": datetime.now().isoformat(),
                            "source": "ollama",
                            "ollama_name": om["id"]
                        }
            except Exception as e:
                logger.warning(f"No se pudieron obtener modelos de Ollama: {e}")

        # Actualizar configuración
        if "local_providers" not in self.config:
            self.config["local_providers"] = {}
        if category not in self.config["local_providers"]:
            self.config["local_providers"][category] = {}
        self.config["local_providers"][category]["installed"] = models

        # Seleccionar primer modelo como activo si no hay
        if not self.config["local_providers"][category].get("selected_model") and models:
            first_model = list(models.keys())[0]
            self.config["local_providers"][category]["selected_model"] = first_model

        return models

    def _is_valid_model_directory(self, path: Path, category: str) -> bool:
        """Determina si un directorio contiene un modelo válido para la categoría."""
        if not path.is_dir():
            return False
        # Marcadores típicos según categoría
        markers = {
            "text": ["config.json", "pytorch_model.bin", "model.safetensors"],
            "image": ["model_index.json", "unet", "vae"],
            "tts": ["config.json", "model.safetensors", "pytorch_model.bin"]  # Kokoro puede variar
        }
        required = markers.get(category, ["config.json"])
        for marker in required:
            if (path / marker).exists() or any(path.glob(marker)):
                return True
        return False

    def _get_directory_size_mb(self, path: Path) -> float:
        """Calcula el tamaño total en MB de un directorio."""
        total = 0
        for f in path.rglob('*'):
            if f.is_file():
                total += f.stat().st_size
        return total / (1024 * 1024)

    def _guess_model_id(self, folder: Path, category: str) -> str | None:
        """Intenta adivinar el model_id a partir del nombre de la carpeta."""
        # Podríamos guardar un archivo metadata.json al descargar, pero como fallback usamos el nombre
        folder_name = folder.name
        # Si coincide con el model_id configurado, usarlo
        cat_config = self.config.get("local_providers", {}).get(category, {})
        if cat_config.get("model_id", "").replace("/", "--") == folder_name:
            return cat_config["model_id"]
        # Buscar en catálogo
        for model in self.catalog.get(category, []):
            if model["id"].replace("/", "--") == folder_name:
                return model["id"]
        return folder_name.replace("--", "/")

    def _get_display_name(self, model_id: str, category: str) -> str:
        """Obtiene el nombre para mostrar desde el catálogo o genera uno."""
        for model in self.catalog.get(category, []):
            if model["id"] == model_id:
                return model["name"]
        return model_id.split("/")[-1]

    def get_available_catalog(self, category: str) -> list[dict]:
        """Devuelve la lista de modelos del catálogo para una categoría."""
        return self.catalog.get(category, [])

    # ------------------------------------------------------------------
    # Métodos de descarga
    # ------------------------------------------------------------------
    def download_model(
        self,
        category: str,
        model_id: str,
        progress_callback: Callable[[float, str], None] | None = None
    ) -> bool:
        """Descarga un modelo usando snapshot_download, con espacio verificado (sin RAM)."""
        with self._download_lock:
            cancel_event = threading.Event()
            self._cancel_flags[model_id] = cancel_event

            try:
                local_path = get_model_path(category, self.config)
                if not local_path:
                    raise ValueError(f"No se pudo determinar la ruta local para {category}")

                model_folder = local_path / model_id.replace("/", "--")
                model_folder.mkdir(parents=True, exist_ok=True)

                # Verificar espacio en disco
                model_info = next(
                    (m for m in self.get_available_catalog(category) if m["id"] == model_id),
                    None
                )
                if model_info:
                    required_bytes = model_info["size_gb"] * 1024 * 1024 * 1024 * 1.5
                    free_bytes = shutil.disk_usage(model_folder).free
                    if free_bytes < required_bytes:
                        raise OSError(
                            f"Espacio insuficiente. Necesitas {required_bytes/1e9:.1f} GB, "
                            f"tienes {free_bytes/1e9:.1f} GB."
                        )

                # Descargar usando snapshot_download (la autenticación se maneja globalmente en main.py)
                snapshot_download(
                    repo_id=model_id,
                    local_dir=str(model_folder),
                    max_workers=4,
                    local_dir_use_symlinks=False,
                    resume_download=True,
                )

                if cancel_event.is_set():
                    logger.info(f"Descarga de {model_id} cancelada por el usuario.")
                    return False

                self._update_installed_metadata(category, model_id, model_folder)
                self.scan_installed_models(category)

                if progress_callback:
                    progress_callback(1.0, "Completado")
                return True

            except Exception as e:
                logger.error(f"Error descargando {model_id}: {e}")
                if progress_callback:
                    progress_callback(0.0, f"Error: {str(e)[:50]}")
                return False
            finally:
                self._cancel_flags.pop(model_id, None)

    def cancel_download(self, model_id: str):
        if model_id in self._cancel_flags:
            self._cancel_flags[model_id].set()

    def _update_installed_metadata(self, category: str, model_id: str, folder: Path):
        """Guarda metadatos del modelo instalado en la configuración."""
        size_mb = sum(f.stat().st_size for f in folder.rglob('*') if f.is_file()) / (1024 * 1024)
        if "local_providers" not in self.config:
            self.config["local_providers"] = {}
        if category not in self.config["local_providers"]:
            self.config["local_providers"][category] = {}
        if "installed" not in self.config["local_providers"][category]:
            self.config["local_providers"][category]["installed"] = {}

        self.config["local_providers"][category]["installed"][model_id] = {
            "path": str(folder),
            "display_name": self._get_display_name(model_id, category),
            "size_mb": size_mb,
            "installed_date": datetime.now().isoformat()
        }

        # Si no hay modelo activo, establecer este
        if not self.config["local_providers"][category].get("selected_model"):
            self.config["local_providers"][category]["selected_model"] = model_id

    # ------------------------------------------------------------------
    # Métodos de eliminación
    # ------------------------------------------------------------------
    def delete_model(self, category: str, model_id: str) -> bool:
        """Elimina un modelo instalado y actualiza la configuración."""
        installed = self.config.get("local_providers", {}).get(category, {}).get("installed", {})
        if model_id not in installed:
            logger.warning(f"Modelo {model_id} no encontrado en instalados.")
            return False

        model_path = Path(installed[model_id]["path"])
        if not model_path.exists():
            logger.warning(f"La carpeta del modelo {model_path} no existe.")
            # Eliminar de la lista de todas formas
            del self.config["local_providers"][category]["installed"][model_id]
            return True

        try:
            shutil.rmtree(model_path)
            logger.info(f"Modelo {model_id} eliminado de {model_path}")

            # Actualizar configuración
            del self.config["local_providers"][category]["installed"][model_id]

            # Si era el modelo activo, seleccionar otro si existe
            if self.config["local_providers"][category].get("selected_model") == model_id:
                remaining = list(self.config["local_providers"][category]["installed"].keys())
                if remaining:
                    self.config["local_providers"][category]["selected_model"] = remaining[0]
                else:
                    self.config["local_providers"][category]["selected_model"] = ""

            return True
        except Exception as e:
            logger.error(f"Error eliminando modelo {model_id}: {e}")
            return False

    # ------------------------------------------------------------------
    # Gestión del modelo activo
    # ------------------------------------------------------------------
    def set_active_model(self, category: str, model_id: str) -> bool:
        """Establece el modelo activo para una categoría."""
        installed = self.config.get("local_providers", {}).get(category, {}).get("installed", {})
        if model_id not in installed:
            logger.error(f"Modelo {model_id} no está instalado en {category}.")
            return False

        if "local_providers" not in self.config:
            self.config["local_providers"] = {}
        if category not in self.config["local_providers"]:
            self.config["local_providers"][category] = {}

        self.config["local_providers"][category]["selected_model"] = model_id
        logger.info(f"Modelo activo para {category}: {model_id}")
        return True

    def get_active_model(self, category: str) -> str | None:
        """Devuelve el model_id del modelo activo para una categoría."""
        return self.config.get("local_providers", {}).get(category, {}).get("selected_model")

    def get_active_model_path(self, category: str) -> Path | None:
        """Devuelve la ruta del modelo activo para una categoría."""
        model_id = self.get_active_model(category)
        if not model_id:
            return None
        installed = self.config.get("local_providers", {}).get(category, {}).get("installed", {})
        if model_id in installed:
            return Path(installed[model_id]["path"])
        return None

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    def is_model_installed(self, category: str, model_id: str) -> bool:
        """Verifica si un modelo específico está instalado."""
        installed = self.config.get("local_providers", {}).get(category, {}).get("installed", {})
        return model_id in installed

    def get_total_size(self, category: str | None = None) -> float:
        """Devuelve el tamaño total en MB de los modelos instalados."""
        total = 0.0
        cats = [category] if category else CATEGORIES
        for cat in cats:
            installed = self.config.get("local_providers", {}).get(cat, {}).get("installed", {})
            for model_info in installed.values():
                total += model_info.get("size_mb", 0)
        return total

    def save_config(self):
        """Guarda la configuración actualizada (debe ser llamado por el config_manager)."""
        from src.config_manager import save_config
        return save_config(self.config)
