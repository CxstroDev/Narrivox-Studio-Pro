import logging
from src.engines.image.pollinations import PollinationsProvider
from src.engines.image.zimage import ZImageProvider
from src.engines.image.huggingface import HuggingFaceProvider
from src.engines.image.local import LocalImageProvider
from src.engines.image.cloudflare import CloudflareProvider
try:
    from src.engines.image.puter import PuterProvider
except ImportError:
    # Puter es opcional: su ausencia no debe impedir usar los demás proveedores.
    PuterProvider = None

logger = logging.getLogger("Narrivox")

class ImageEngine:
    """
    Motor principal de imágenes que actúa como fachada y gestiona fallbacks.
    Ahora utiliza proveedores abstraídos.
    """
    def __init__(self, config: dict):
        self.config = config
        self.provider = config.get("image_provider", "pollinations")
        
        # Mapa de proveedores
        self._providers = {
            "pollinations": PollinationsProvider(config),
            "zimage": ZImageProvider(config),
            "huggingface": HuggingFaceProvider(config),
            "cloudflare": CloudflareProvider(config),
            "local": LocalImageProvider(config)
        }
        if PuterProvider is not None:
            self._providers["puter"] = PuterProvider(config)

    def generate(self, prompt: str, negative_prompt: str = "", model_id: str = None, callback=None) -> bytes:
        providers_to_try = [self.provider]
        for p in ["zimage", "huggingface", "pollinations", "cloudflare", "puter"]:
            if p not in providers_to_try:
                providers_to_try.append(p)

        # Intentar cada proveedor y retornar al primer éxito
        for provider_name in providers_to_try:
            provider = self._providers.get(provider_name)
            if not provider:
                continue
                
            logger.info(f"Probando {provider_name} para: {prompt[:40]}...")
            
            try:
                kwargs = {"model_id": model_id} if model_id else {}
                # No pasar el callback al proveedor para que no interfiera con la lógica bloqueante aquí
                # El callback lo gestionamos en el caller
                result = provider.generate(prompt, negative_prompt, **kwargs)
                
                if result:
                    logger.info(f"Éxito con {provider_name}")
                    if callback:
                        callback(result, True, "")
                    return result
            except Exception as e:
                logger.warning(f"Error en {provider_name}: {str(e)[:50]}")
                continue

        # Si llegamos aquí, ninguno funcionó
        err_msg = "Todos los proveedores fallaron."
        logger.error(err_msg)
        if callback:
            callback(None, False, err_msg)
        raise Exception(err_msg)
