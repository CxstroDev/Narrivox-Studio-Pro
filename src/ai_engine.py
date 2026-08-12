import logging
import threading
from src.engines.text.groq_provider import GroqProvider
from src.engines.text.openai_provider import OpenAICompatibleProvider
from src.engines.text.gemini_provider import GeminiProvider

logger = logging.getLogger("Narrivox")

class AIEngine:
    """
    Motor principal de IA que gestiona proveedores de texto y fallbacks.
    Arquitectura modular basada en proveedores.
    """
    def __init__(self, config: dict):
        self.config = config
        self.provider_name = config.get("ia_provider", "groq")
        self._lock = threading.Lock()
        self._cancel_event = threading.Event()
        self._current_thread = None
        
        # Inicializar proveedores
        self._providers = {
            "groq": GroqProvider(config),
            "openai": OpenAICompatibleProvider(config, "openai"),
            "deepseek": OpenAICompatibleProvider(config, "deepseek"),
            "openrouter": OpenAICompatibleProvider(config, "openrouter"),
            "ollama": OpenAICompatibleProvider(config, "ollama"),
            "gemini": GeminiProvider(config)
        }

    def generate_script(self, prompt: str, callback, on_progress=None, timeout: int = 60):
        """Genera un guion usando el sistema de fallback."""
        system_msg = "Eres un guionista experto en narrativa de misterio y ciencia ficción."
        self.generate_with_fallback(prompt, system_msg, callback, on_progress, timeout)

    def generate_script_with_context(self, system_msg: str, user_prompt: str, callback, on_progress=None, timeout: int = 60):
        """Genera un guion con contexto específico."""
        self.generate_with_fallback(user_prompt, system_msg, callback, on_progress, timeout)

    def generate_with_fallback(self, prompt, system_msg="", callback=None, on_progress=None, timeout=60):
        if not callback:
            raise ValueError("Se requiere un callback")

        self.cancel_current_task()
        with self._lock:
            self._cancel_event.clear()

        # Determinar cadena de fallback
        if self.config.get("enable_fallback", False):
            fallback_chain = self.config.get("ai_fallback_chain", [])
        else:
            fallback_chain = [{"provider": self.provider_name, "model": self.config.get("ia_model")}]

        def task():
            last_error = None
            for step in fallback_chain:
                if self._cancel_event.is_set():
                    self._safe_callback(callback, "", False, True)
                    return

                p_name = step["provider"]
                if on_progress:
                    self._safe_callback(on_progress, f"Intentando con {p_name}...")

                try:
                    provider = self._providers.get(p_name)
                    if not provider:
                        continue
                    
                    logger.info(f"Generando texto con {p_name}")
                    # Envolver el callback del proveedor para capturar el resultado
                    def provider_callback(res, success, cancelled):
                        if success:
                            self._safe_callback(callback, res, True, False)
                        else:
                            raise Exception(res)

                    provider.generate(prompt, system_msg, provider_callback)
                    return # Éxito, terminamos
                except Exception as e:
                    logger.warning(f"Fallo con {p_name}: {e}")
                    last_error = e
                    continue

            error_msg = f"Todos los proveedores fallaron. Último error: {last_error}"
            self._safe_callback(callback, error_msg, False, False)

        self._current_thread = threading.Thread(target=task, daemon=True)
        self._current_thread.start()

    def _safe_callback(self, callback, *args):
        if not callable(callback): return
        try:
            import tkinter as tk
            root = getattr(tk, '_default_root', None)
            if root and root.winfo_exists():
                root.after(0, lambda: callback(*args))
            else:
                callback(*args)
        except Exception:
            callback(*args)

    def cancel_current_task(self):
        with self._lock:
            if self._current_thread and self._current_thread.is_alive():
                self._cancel_event.set()
                self._current_thread.join(timeout=0.5)
            self._current_thread = None

    def format_prompt(self, template: str, data: dict) -> str:
        try:
            return template.format(**data)
        except KeyError as e:
            return f"Error: falta {e}"
