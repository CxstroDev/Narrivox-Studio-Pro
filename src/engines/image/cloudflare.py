import os
import base64
import requests
from src.engines.image.base import ImageProviderBase, logger

class CloudflareProvider(ImageProviderBase):
    """Proveedor utilizando Cloudflare Workers AI."""

    def generate(self, prompt: str, negative_prompt: str = "", callback=None, **kwargs) -> bytes:
        account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        api_token = os.getenv("CLOUDFLARE_API_TOKEN")
        if not account_id or not api_token:
            raise Exception("Cloudflare credenciales no encontradas en .env")

        # Modelo predeterminado: @cf/black-forest-labs/flux-1-schnell
        model = kwargs.get("model_id", "@cf/black-forest-labs/flux-1-schnell")
        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
        
        payload = {"prompt": prompt}
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt

        response = requests.post(url, headers={"Authorization": f"Bearer {api_token}"}, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json().get("result", {})
            img_b64 = result.get("image")
            if img_b64:
                img_bytes = base64.b64decode(img_b64)
                if callback: callback(img_bytes, True, "")
                return img_bytes
        
        error_msg = f"Cloudflare error {response.status_code}: {response.text}"
        logger.error(error_msg)
        raise Exception(error_msg)
