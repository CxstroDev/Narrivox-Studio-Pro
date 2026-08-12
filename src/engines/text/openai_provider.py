from openai import OpenAI
from src.engines.text.base import TextProviderBase, logger

class OpenAICompatibleProvider(TextProviderBase):
    """Proveedor para servicios compatibles con OpenAI (OpenAI, DeepSeek, OpenRouter, Ollama)."""
    
    def __init__(self, config: dict, provider_name: str):
        super().__init__(config)
        self.provider_name = provider_name
        self._setup_client()

    def _setup_client(self):
        if self.provider_name == "openai":
            api_key = self.config.get("openai_api_key", "")
            base_url = self.config.get("openai_base_url", "https://api.openai.com/v1")
        elif self.provider_name == "deepseek":
            api_key = self.config.get("deepseek_api_key", "")
            base_url = "https://api.deepseek.com/v1"
        elif self.provider_name == "openrouter":
            api_key = self.config.get("openrouter_api_key", "")
            base_url = "https://openrouter.ai/api/v1"
        elif self.provider_name == "ollama":
            api_key = "ollama"
            base_url = self.config.get("ollama_base_url", "http://localhost:11434/v1")
        else:
            raise ValueError(f"Proveedor desconocido: {self.provider_name}")

        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, prompt: str, system_msg: str = "", callback=None, **kwargs) -> None:
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ]
        
        try:
            # Seleccionar modelo según proveedor
            model_key = f"ia_model" # Por defecto
            if self.provider_name == "ollama":
                model = "llama3"
            else:
                model = self.config.get(model_key, "gpt-4o")

            completion = self.client.chat.completions.create(
                model=model,
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
