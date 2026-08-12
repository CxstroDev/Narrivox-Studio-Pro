import puter
from src.engines.image.base import ImageProviderBase, logger

class PuterProvider(ImageProviderBase):
    """Proveedor utilizando el SDK de Puter.js."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.ai = puter.ai # Acceso al cliente de IA
        
    def generate(self, prompt: str, negative_prompt: str = "", callback=None, **kwargs) -> bytes:
        model = kwargs.get("model_id") or "stabilityai/stable-diffusion-xl-base-1.0"
        
        try:
            logger.info(f"Generando con Puter (SDK) ({model}): {prompt[:50]}...")
            
            # El SDK actual de Puter parece centrado en Chat/Conversacional.
            # Verificamos si existe un método de generación de imagen.
            # Si no, Puter puede requerir una implementación vía CDN JS.
            # Por ahora, usamos el SDK para intentar una llamada a 'chat' o similar 
            # si 'txt2img' no está disponible.
            
            # NOTA: Dada la limitación del SDK detectada, informamos del problema
            raise Exception("El SDK de Python de Puter no soporta generación de imágenes (solo chat).")
            
        except Exception as e:
            logger.error(f"Error generando con Puter: {e}")
            if callback:
                callback(None, False, str(e))
            raise e
