# src/local_text_engine.py
import gc
import logging
import threading
import weakref
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from src.model_utils import lazy_import_torch, lazy_import_transformers
from src.ollama_client import OllamaClient

logger = logging.getLogger("Narrivox")

class LocalTextEngine:
    # Singleton pattern para gestión de memoria
    _instances = weakref.WeakValueDictionary()
    _cleanup_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        instance_id = id(args[0]) if args else id(kwargs)
        if instance_id not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[instance_id] = instance
        return cls._instances[instance_id]
    def __init__(self, config: dict):
        self.config = config
        self.model = None
        self.tokenizer = None
        self._cancel_event = threading.Event()
        self._load_lock = threading.Lock()
        self._generation_lock = threading.Lock()  # Evitar generaciones simultáneas
        self._last_used_time = 0
        self._memory_cleanup_threshold = 300  # 5 minutos sin uso

        # Obtener modelo activo desde configuración
        text_config = config.get("local_providers", {}).get("text", {})
        self.model_id = text_config.get("selected_model") or text_config.get("model_id", "Qwen/Qwen2.5-1.5B-Instruct")
        self.device = text_config.get("device", "cpu")
        self.max_memory_mb = text_config.get("max_memory_mb", 4096)  # Límite de memoria

        # Determinar si usa Ollama
        self.use_ollama = self.model_id.startswith("ollama:")
        if self.use_ollama:
            self.ollama_client = OllamaClient()
            self.ollama_model_name = self.model_id.replace("ollama:", "")

        # Determinar ruta real del modelo
        installed = text_config.get("installed", {})
        if self.model_id in installed:
            self.model_path = Path(installed[self.model_id]["path"])
        else:
            # Fallback a ruta antigua
            local_path = text_config.get("local_path", "models/qwen2.5-1.5b-instruct")
            self.model_path = Path(__file__).parent.parent / local_path

        # Registrar para limpieza automática
        self._register_for_cleanup()

    def _register_for_cleanup(self):
        """Registra la instancia para limpieza automática de memoria."""
        def cleanup_worker():
            import time
            while True:
                time.sleep(60)  # Verificar cada minuto
                self._check_and_cleanup_memory()

        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()

    def _check_and_cleanup_memory(self):
        """Verifica y libera memoria si el modelo no se ha usado recientemente."""
        import time
        current_time = time.time()
        if self.model is not None and (current_time - self._last_used_time) > self._memory_cleanup_threshold:
            logger.info("Liberando memoria del modelo de texto por inactividad")
            self._unload_model()

    def _unload_model(self):
        """Descarga el modelo de memoria de forma segura."""
        with self._load_lock:
            if self.model is not None:
                try:
                    del self.model
                    self.model = None
                except Exception as e:
                    logger.debug(f"Error al descargar modelo: {e}")

            if self.tokenizer is not None:
                try:
                    del self.tokenizer
                    self.tokenizer = None
                except Exception as e:
                    logger.debug(f"Error al descargar tokenizer: {e}")

            # Forzar garbage collection
            gc.collect()
            logger.info("Modelo de texto descargado de memoria")

    @contextmanager
    def _memory_context(self):
        """Context manager para gestionar memoria durante generaciones."""
        import time
        self._last_used_time = time.time()
        try:
            yield
        finally:
            # Pequeña pausa para permitir liberación de recursos
            if self.device == "cpu":
                gc.collect()

    def _check_memory_available(self) -> bool:
        """Verifica si hay suficiente memoria disponible."""
        try:
            import psutil
            available_memory = psutil.virtual_memory().available
            required_memory = self.max_memory_mb * 1024 * 1024
            return available_memory >= required_memory
        except ImportError:
            logger.warning("psutil no disponible, no se puede verificar memoria")
            return True
        except Exception as e:
            logger.warning(f"Error verificando memoria: {e}")
            return True

    def _ensure_model_loaded(self):
        if self.model is not None:
            self._last_used_time = __import__('time').time()
            return True

        if not self._check_memory_available():
            raise MemoryError("Memoria insuficiente para cargar el modelo")

        with self._load_lock:
            # Doble check después de adquirir el lock
            if self.model is not None:
                return True

            try:
                torch = lazy_import_torch()
                transformers = lazy_import_transformers()

                logger.info(f"Cargando modelo de texto {self.model_id} desde {self.model_path}...")

                self.tokenizer = transformers.AutoTokenizer.from_pretrained(
                    str(self.model_path),
                    trust_remote_code=True
                )

                load_kwargs = {
                    "torch_dtype": torch.float32,
                    "trust_remote_code": True,
                }
                if self.device == "cpu":
                    load_kwargs["device_map"] = "cpu"
                    load_kwargs["low_cpu_mem_usage"] = True
                else:
                    load_kwargs["device_map"] = "auto"

                self.model = transformers.AutoModelForCausalLM.from_pretrained(
                    str(self.model_path),
                    **load_kwargs
                )

                # Poner el modelo en modo evaluación
                self.model.eval()

                logger.info("Modelo de texto local cargado exitosamente.")
                return True

            except Exception as e:
                logger.error(f"Error cargando modelo local de texto: {e}")
                # Limpiar recursos en caso de error
                self._unload_model()
                raise

    def generate(
        self,
        prompt: str,
        system_msg: str = "",
        callback: Callable[[str, bool, bool], None] | None = None,
        max_new_tokens: int = 1024,
        temperature: float = 0.7
    ) -> None:
        """
        Genera texto usando Qwen 2.5 local.
        El callback se llama con (resultado, éxito, cancelado).
        """
        if not callback:
            raise ValueError("Se requiere un callback")

        self._cancel_event.clear()

        if self.use_ollama:
            self._generate_ollama(prompt, system_msg, callback)
        else:

            def task():
                # Usar lock para evitar generaciones simultáneas
                with self._generation_lock:
                    try:
                        with self._memory_context():
                            if not self._ensure_model_loaded():
                                callback("", False, False)
                                return

                            torch = lazy_import_torch()

                            # Validar longitud del prompt
                            if len(prompt) > 10000:
                                logger.warning("Prompt muy largo, truncando a 10000 caracteres")
                                prompt = prompt[:10000]

                            # Construir mensaje estilo chat
                            messages = []
                            if system_msg:
                                messages.append({"role": "system", "content": system_msg})
                            messages.append({"role": "user", "content": prompt})

                            text = self.tokenizer.apply_chat_template(
                                messages,
                                tokenize=False,
                                add_generation_prompt=True
                            )

                            inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

                            # Verificar cancelación antes de generar
                            if self._cancel_event.is_set():
                                callback("", False, True)
                                return

                            with torch.no_grad():
                                outputs = self.model.generate(
                                    **inputs,
                                    max_new_tokens=max_new_tokens,
                                    temperature=temperature,
                                    do_sample=True,
                                    top_p=0.95,
                                    pad_token_id=self.tokenizer.eos_token_id,
                                    # Optimizaciones para CPU
                                    use_cache=True,
                                )

                            # Verificar cancelación después de generar
                            if self._cancel_event.is_set():
                                callback("", False, True)
                                return

                            response = self.tokenizer.decode(
                                outputs[0][len(inputs[0]):],
                                skip_special_tokens=True
                            )

                            # Limpiar tensors de memoria
                            del inputs, outputs
                            if torch.cuda.is_available():
                                torch.cuda.empty_cache()

                            callback(response, True, False)

                    except MemoryError as e:
                        logger.error(f"Error de memoria: {e}")
                        self._unload_model()
                        callback(f"Error de memoria: {str(e)}", False, False)
                    except Exception as e:
                        logger.error(f"Error en generación local: {e}")
                        callback(f"Error: {str(e)}", False, False)

            threading.Thread(target=task, daemon=True).start()

    def _generate_ollama(self, prompt, system_msg, callback):
        def task():
            try:
                if not self.ollama_client.is_server_running():
                    raise ConnectionError("Servidor Ollama no disponible")
                result = self.ollama_client.generate(
                    model=self.ollama_model_name,
                    prompt=prompt,
                    system_msg=system_msg
                )
                if callback:
                    callback(result, True, False)
            except Exception as e:
                logger.error(f"Error generando con Ollama: {e}")
                if callback:
                    callback(str(e), False, False)
        threading.Thread(target=task, daemon=True).start()

    def cancel(self):
        """Cancela la generación en curso."""
        self._cancel_event.set()

    def cleanup(self):
        """Limpia todos los recursos de forma explícita."""
        logger.info("Limpiando recursos de LocalTextEngine")
        self._unload_model()
        self._cancel_event.set()

    def get_memory_usage(self) -> dict:
        """Obtiene información sobre el uso de memoria."""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return {
                "rss_mb": memory_info.rss / 1024 / 1024,
                "vms_mb": memory_info.vms / 1024 / 1024,
                "model_loaded": self.model is not None,
                "device": self.device
            }
        except ImportError:
            return {
                "model_loaded": self.model is not None,
                "device": self.device,
                "error": "psutil no disponible"
            }
