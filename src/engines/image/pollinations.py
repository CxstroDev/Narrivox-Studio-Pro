import requests
import urllib.parse
import secrets
from src.engines.image.base import ImageProviderBase, logger

class PollinationsProvider(ImageProviderBase):
    """Proveedor de imágenes usando Pollinations.ai."""
    
    def generate(self, prompt: str, negative_prompt: str = "", callback=None, **kwargs) -> bytes:
        # Mejorar el prompt con el negative prompt si existe
        full_prompt = prompt
        if negative_prompt:
            # Pollinations simple API no tiene un parámetro formal de negative_prompt, 
            # se suele añadir al final con delimitadores.
            full_prompt += f" ### negative_prompt: {negative_prompt}"
            
        encoded_prompt = urllib.parse.quote(full_prompt)
        model = kwargs.get("model_id") or self.config.get("pollinations_model", "flux")
        
        # Endpoint optimizado (image.pollinations.ai es más directo)
        seed = kwargs.get("seed") or secrets.randbelow(999999)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&seed={seed}&model={model}&nologo=true"

        try:
            logger.info(f"Generando imagen en Pollinations: {model}")
            response = requests.get(url, timeout=60)
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'image' in content_type:
                    logger.info("Imagen generada con Pollinations.ai")
                    img_bytes = response.content
                    if callback:
                        callback(img_bytes, True, "")
                    return img_bytes
                else:
                    raise Exception(f"Pollinations no devolvió una imagen. Content-Type: {content_type}")
            else:
                # Manejar error 429 específicamente para el gestor
                if response.status_code == 429:
                    raise Exception("429: Pollinations saturado")
                raise Exception(f"Pollinations.ai error {response.status_code}")
        except Exception as e:
            if callback:
                callback(None, False, str(e))
            raise e
