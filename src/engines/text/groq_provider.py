from groq import Groq
from src.engines.text.base import TextProviderBase, logger

class GroqProvider(TextProviderBase):
    """Proveedor de texto usando Groq."""
    
    def generate(self, prompt: str, system_msg: str = "", callback=None, **kwargs) -> None:
        api_key = self.config.get("api_key", "")
        if not api_key:
            raise ValueError("API Key de Groq no configurada")

        client = Groq(api_key=api_key)
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ]
        
        try:
            completion = client.chat.completions.create(
                model=self.config.get("ia_model", "llama-3.3-70b-versatile"),
                messages=messages,
                temperature=self.config.get("ia_temp", 0.7),
            )
            result = completion.choices[0].message.content
            if callback:
                callback(result, True, False)
        except Exception as e:
            if callback:
                callback(str(e), False, False)
            raise e
