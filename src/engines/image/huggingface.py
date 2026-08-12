import requests
from src.engines.image.base import ImageProviderBase, logger

class HuggingFaceProvider(ImageProviderBase):
    """Proveedor de imágenes usando Hugging Face Inference API."""
    
    def generate(self, prompt: str, negative_prompt: str = "", callback=None, **kwargs) -> bytes:
        hf_token = self.config.get("hf_token", "").strip()
        if not hf_token:
            raise Exception("Token de Hugging Face no configurado.")

        model_id = kwargs.get("model_id")
        # Validación robusta de modelo
        if not model_id or model_id == "Default Space" or "/" not in model_id:
            model_id = self.config.get("hf_model_id", "stabilityai/stable-diffusion-xl-base-1.0")

        api_url = f"https://api-inference.huggingface.co/models/{model_id}"
        headers = {"Authorization": f"Bearer {hf_token}"}

        payload = {"inputs": prompt}
        if negative_prompt:
            payload["parameters"] = {"negative_prompt": negative_prompt}

        try:
            logger.info(f"HuggingFace Request to {api_url} with model {model_id}")
            response = requests.post(api_url, headers=headers, json=payload, timeout=120)

            if response.status_code == 200:
                img_bytes = response.content
                # Verificar si es un error escondido en el contenido
                if len(img_bytes) < 100 and b"error" in img_bytes:
                    raise Exception(f"HF API returned internal error: {img_bytes.decode()}")

                if callback:
                    callback(img_bytes, True, "")
                return img_bytes
            else:
                logger.error(f"HF Status: {response.status_code}, Response: {response.text}")
                raise Exception(f"HF Error {response.status_code}: {response.text[:100]}")

        except Exception as e:
            if callback:
                callback(None, False, str(e))
            raise e
