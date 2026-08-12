# src/model_downloader.py
import logging
import time
from collections.abc import Callable
from pathlib import Path

from huggingface_hub import snapshot_download

logger = logging.getLogger("Narrivox")

class ModelDownloader:
    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir

    def download_model(
        self,
        model_id: str,
        local_path: Path,
        progress_callback: Callable[[float, str], None] | None = None,
        max_retries: int = 3
    ) -> bool:
        """
        Descarga un modelo de Hugging Face.
        """
        for attempt in range(max_retries):
            try:
                local_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Descargando {model_id} en {local_path}...")

                snapshot_download(
                    repo_id=model_id,
                    local_dir=str(local_path),
                    local_dir_use_symlinks=False,
                    resume_download=True,
                    max_workers=4,
                )
                logger.info(f"Modelo {model_id} descargado exitosamente.")
                if progress_callback:
                    progress_callback(1.0, "Completado")
                return True
            except Exception as e:
                logger.error(f"Intento {attempt+1} falló: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                else:
                    if progress_callback:
                        progress_callback(0.0, f"Error: {str(e)[:50]}")
                    return False
        return False
