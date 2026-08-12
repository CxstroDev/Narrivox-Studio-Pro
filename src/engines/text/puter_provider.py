import puter
from src.engines.text.base import TextProviderBase, logger

class PuterProvider(TextProviderBase):
    """Proveedor de texto usando el SDK de Puter.js (chat)."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        try:
            import puter
            self.puter_ai = puter.ai
            self.puter_client_available = True
        except ImportError:
            self.puter_client_available = False
            logger.warning("puter-python-sdk no instalado. PuterProvider de texto no estará disponible.")

    def generate(self, prompt: str, system_msg: str = "", **kwargs) -> str:
        if not self.puter_client_available:
            raise Exception("puter-python-sdk no está instalado.")

        model = kwargs.get("model_id") or "gpt-2" # Modelo por defecto
        
        try:
            logger.info(f"Generando texto con Puter ({model}): {prompt[:50]}...")
            
            # Usamos el método 'chat' del SDK.
            # Nota: La llamada puede ser asíncrona. Si es así, se necesitará `asyncio.run()`
            # o similar para mantener el hilo principal responsivo.
            response = self.puter_ai.chat(
                prompt=prompt,
                model=model,
                system_msg=system_msg 
            )
            
            # Procesar la respuesta: el SDK suele devolver un dict o string
            if isinstance(response, dict):
                generated_text = response.get("text") or response.get("message", "")
            elif isinstance(response, str):
                generated_text = response
            else:
                generated_text = str(response) # Fallback a string

            if not generated_text:
                raise Exception("Puter API no devolvió texto.")

            logger.info(f"Texto de Puter recibido: {generated_text[:50]}...")
            return generated_text.strip()
            
        except AttributeError:
            logger.error("SDK de Puter: Método 'chat' no encontrado o estructura inesperada.")
            raise Exception("SDK de Puter incompatible con el método 'chat'.")
        except Exception as e:
            logger.error(f"Error generando texto con Puter: {e}")
            raise e
