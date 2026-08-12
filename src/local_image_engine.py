# src/local_image_engine.py
import gc
import logging
import threading
import weakref
from collections.abc import Callable
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from typing import Optional

logger = logging.getLogger("Narrivox")

class LocalImageEngine:
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
        self.pipe = None
        self._cancel_event = threading.Event()
        self._load_lock = threading.Lock()
        self._generation_lock = threading.Lock()
        self._last_used_time = 0
        self._memory_cleanup_threshold = 300  # 5 minutos sin uso

        img_config = config.get("local_providers", {}).get("image", {})
        self.model_id = img_config.get("selected_model") or img_config.get("model_id", "OFA-Sys/small-stable-diffusion-v0")
        self.device = img_config.get("device", "cpu")
        self.max_memory_mb = img_config.get("max_memory_mb", 6144)  # 6GB para imágenes

        installed = img_config.get("installed", {})
        if self.model_id in installed:
            self.model_path = Path(installed[self.model_id]["path"])
        else:
            local_path = img_config.get("local_path", "models/small-sd-v0")
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
        if self.pipe is not None and (current_time - self._last_used_time) > self._memory_cleanup_threshold:
            logger.info("Liberando memoria del modelo de imagen por inactividad")
            self._unload_model()

    def _unload_model(self):
        """Descarga el modelo de memoria de forma segura."""
        with self._load_lock:
            if self.pipe is not None:
                try:
                    # Mover a CPU primero si está en GPU
                    if hasattr(self.pipe, 'device'):
                        import torch
                        device = self.pipe.device
                        if device.type == 'cuda':
                            self.pipe.to('cpu')

                    del self.pipe
                    self.pipe = None
                except Exception as e:
                    logger.debug(f"Error al descargar modelo: {e}")

            # Forzar garbage collection
            gc.collect()
            logger.info("Modelo de imagen descargado de memoria")

    @contextmanager
    def _memory_context(self):
        """Context manager para gestionar memoria durante generaciones."""
        import time
        self._last_used_time = time.time()
        try:
            yield
        finally:
            # Liberar memoria después de la generación
            if self.device == "cpu":
                gc.collect()
            else:
                try:
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except ImportError:
                    pass

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
        if self.pipe is not None:
            self._last_used_time = __import__('time').time()
            return True

        if not self._check_memory_available():
            raise MemoryError("Memoria insuficiente para cargar el modelo")

        with self._load_lock:
            # Doble check después de adquirir el lock
            if self.pipe is not None:
                return True

            try:
                import torch
                from diffusers import StableDiffusionPipeline

                logger.info(f"Cargando modelo de imagen {self.model_id} desde {self.model_path}...")

                load_kwargs = {
                    "torch_dtype": torch.float32,
                    "safety_checker": None,
                    "requires_safety_checker": False,
                }

                if self.device == "cpu":
                    load_kwargs["low_cpu_mem_usage"] = True
                else:
                    load_kwargs["variant"] = "fp16"

                self.pipe = StableDiffusionPipeline.from_pretrained(
                    str(self.model_path),
                    **load_kwargs
                )

                # Optimizaciones específicas por dispositivo
                if self.device == "cpu":
                    try:
                        self.pipe.enable_attention_slicing()
                        logger.info("Attention slicing habilitado para CPU")
                    except Exception as e:
                        logger.debug(f"No se pudo habilitar attention slicing: {e}")
                else:
                    try:
                        self.pipe.enable_model_cpu_offload()
                        logger.info("Model CPU offload habilitado para GPU")
                    except Exception as e:
                        logger.debug(f"No se pudo habilitar model CPU offload: {e}")

                logger.info("Modelo de imagen local cargado exitosamente.")
                return True

            except Exception as e:
                logger.error(f"Error cargando modelo de imagen local: {e}")
                # Limpiar recursos en caso de error
                self._unload_model()
                raise

    def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        callback: Callable[[bytes, bool, str], None] | None = None,
        num_inference_steps: int = 15,
        guidance_scale: float = 7.0,
        width: int = 512,
        height: int = 512
    ) -> None:
        """
        Genera una imagen usando Small-SD-V0.
        callback: (image_bytes, success, error_message)
        """
        self._cancel_event.clear()

        def task():
            # Usar lock para evitar generaciones simultáneas
            with self._generation_lock:
                try:
                    with self._memory_context():
                        # Validar parámetros
                        if not prompt or len(prompt.strip()) == 0:
                            if callback:
                                callback(None, False, "El prompt no puede estar vacío")
                            return

                        # Usar una variable local para evitar UnboundLocalError
                        actual_prompt = prompt
                        if len(actual_prompt) > 500:
                            logger.warning("Prompt muy largo, truncando a 500 caracteres")
                            actual_prompt = actual_prompt[:500]

                        self._ensure_model_loaded()

                        import torch

                        # Verificar cancelación antes de generar
                        if self._cancel_event.is_set():
                            if callback:
                                callback(None, False, "Generación cancelada")
                            return

                        with torch.no_grad():
                            result = self.pipe(
                                prompt=actual_prompt,
                                negative_prompt=negative_prompt if negative_prompt else None,
                                num_inference_steps=num_inference_steps,
                                guidance_scale=guidance_scale,
                                width=width,
                                height=height
                            )

                        # Verificar cancelación después de generar
                        if self._cancel_event.is_set():
                            if callback:
                                callback(None, False, "Generación cancelada")
                            return

                        image = result.images[0]

                        # Convertir a bytes con calidad optimizada
                        img_bytes = BytesIO()
                        image.save(img_bytes, format="JPEG", quality=85, optimize=True)

                        logger.info("Imagen local generada exitosamente")
                        if callback:
                            callback(img_bytes.getvalue(), True, "")

                except MemoryError as e:
                    logger.error(f"Error de memoria: {e}")
                    self._unload_model()
                    if callback:
                        callback(None, False, f"Error de memoria: {str(e)}")
                except Exception as e:
                    # 'prompt' está en el scope superior de 'task', así que debería ser accesible
                    # pero lo manejamos de forma segura por si acaso.
                    p_info = prompt[:30] if 'prompt' in locals() and prompt else "desconocido"
                    logger.error(f"Error en generación local de imagen ({p_info}): {e}")
                    if callback:
                        callback(None, False, str(e))

        threading.Thread(target=task, daemon=True).start()

    def cancel(self):
        """Cancela la generación en curso."""
        self._cancel_event.set()

    def cleanup(self):
        """Limpia todos los recursos de forma explícita."""
        logger.info("Limpiando recursos de LocalImageEngine")
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
                "model_loaded": self.pipe is not None,
                "device": self.device
            }
        except ImportError:
            return {
                "model_loaded": self.pipe is not None,
                "device": self.device,
                "error": "psutil no disponible"
            }
