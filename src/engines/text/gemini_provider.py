from src.engines.text.base import TextProviderBase, logger

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class GeminiProvider(TextProviderBase):
    """Proveedor de texto usando Google Gemini."""
    
    def generate(self, prompt: str, system_msg: str = "", callback=None, **kwargs) -> None:
        if not GEMINI_AVAILABLE:
            raise ImportError("google-genai no instalado")

        api_key = self.config.get("gemini_api_key", "")
        if not api_key:
            raise ValueError("API Key de Gemini no configurada")

        client = genai.Client(api_key=api_key)
        
        try:
            # Nota: Gemini soporta system_instruction en versiones recientes
            response = client.models.generate_content(
                model=self.config.get("ia_model", "gemini-2.0-flash"),
                contents=f"{system_msg}\n\n{prompt}"
            )
            result = response.text
            if callback:
                callback(result, True, False)
        except Exception as e:
            if callback:
                callback(str(e), False, False)
            raise e
