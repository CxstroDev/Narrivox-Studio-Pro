import time
import secrets
import threading
from src.engines.image.base import ImageProviderBase, logger

try:
    from gradio_client import Client
    GRADIO_AVAILABLE = True
except ImportError:
    GRADIO_AVAILABLE = False

class ZImageProvider(ImageProviderBase):
    """Proveedor de imágenes usando Z-Image-Turbo vía Gradio."""
    
    _client_cache = {}
    _cache_lock = threading.Lock()
    
    def _get_client(self, space_name: str):
        with self._cache_lock:
            if space_name not in self._client_cache:
                logger.info(f"Conectando a Gradio Space: {space_name}")
                self._client_cache[space_name] = Client(space_name)
            return self._client_cache[space_name]

    def generate(self, prompt: str, negative_prompt: str = "", callback=None, **kwargs) -> bytes:
        if not GRADIO_AVAILABLE:
            raise Exception("gradio_client no instalado.")

        space_name = self.config.get("zimage_space", "mrfakename/Z-Image-Turbo")
        max_retries = kwargs.get("max_retries", 3)
        
        try:
            client = self._get_client(space_name)
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"Intento {attempt + 1}/{max_retries} con {space_name}...")
                    result = client.predict(
                        prompt=prompt,
                        negative_prompt=negative_prompt,
                        seed=secrets.randbelow(999999) if 'secrets' in globals() else 0,
                        randomize_seed=True,
                        width=1024,
                        height=1024,
                        guidance_scale=0,
                        num_inference_steps=2,
                        api_name=None
                    )
                    
                    if result and isinstance(result, tuple) and len(result) > 0:
                        img_path = result[0]
                        with open(img_path, "rb") as f:
                            img_bytes = f.read()
                        if callback:
                            callback(img_bytes, True, "")
                        return img_bytes
                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    raise e
            raise Exception("Fallo tras máximos reintentos en Z-Image")
        except Exception as e:
            if callback:
                callback(None, False, str(e))
            raise e
