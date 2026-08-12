import threading
from src.engines.image.base import ImageProviderBase, logger
from src.local_image_engine import LocalImageEngine
from src.model_utils import is_local_model_available

class LocalImageProvider(ImageProviderBase):
    """Proveedor de imágenes local usando Small Stable Diffusion."""
    
    def generate(self, prompt: str, negative_prompt: str = "", callback=None, **kwargs) -> bytes:
        if not is_local_model_available("image", self.config):
             raise Exception("Modelo local no descargado o no disponible.")
        
        local_engine = LocalImageEngine(self.config)
        result = [None]
        error_msg = [None]
        event = threading.Event()

        def internal_callback(img_bytes, success, error):
            if success:
                result[0] = img_bytes
                if callback: callback(img_bytes, True, "")
            else:
                error_msg[0] = error
                if callback: callback(None, False, error)
            event.set()

        local_engine.generate(prompt, negative_prompt, callback=internal_callback)
        
        # Timeout extendido para CPU
        if not event.wait(timeout=240):
            raise Exception("Timeout (4min) en generación local.")

        if result[0] is None:
            raise Exception(f"Fallo generación local: {error_msg[0]}")
            
        return result[0]
