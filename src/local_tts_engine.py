# src/local_tts_engine.py
"""
Motor TTS local usando Kokoro a través de su API REST (FastAPI).
El servidor debe estar corriendo en http://localhost:8880
"""
import logging
import os
import time
from collections.abc import Callable

import requests

logger = logging.getLogger("Narrivox")

class LocalTTSEngine:
    def __init__(self, config: dict):
        self.config = config
        tts_config = config.get("local_providers", {}).get("tts", {})
        self.model_id = tts_config.get("selected_model") or tts_config.get("model_id", "hexgrad/Kokoro-82M")
        self.port = tts_config.get("port", 8880)
        self.api_url = f"http://localhost:{self.port}"

    def is_server_running(self, timeout: float = 2.0) -> bool:
        """Verifica si el servidor de Kokoro está activo y responde."""
        # Intentar endpoints conocidos
        endpoints = [
            "/v1/audio/speech",      # Endpoint principal de generación (POST)
            "/docs",                 # FastAPI docs
            "/openapi.json",         # OpenAPI spec
            "/"                      # Raíz
        ]
        for endpoint in endpoints:
            try:
                # Usar GET para verificar disponibilidad
                response = requests.get(f"{self.api_url}{endpoint}", timeout=timeout)
                if response.status_code < 500:  # Cualquier respuesta no-error indica que el servidor está vivo
                    logger.info(f"Servidor Kokoro detectado en {self.api_url}{endpoint}")
                    return True
            except requests.exceptions.ConnectionError:
                continue
            except Exception as e:
                logger.debug(f"Error verificando endpoint {endpoint}: {e}")
                continue
        return False

    def wait_for_server(self, max_wait: int = 30, callback: Callable[[str], None] | None = None) -> bool:
        """Espera a que el servidor esté disponible, mostrando progreso."""
        logger.info(f"Esperando servidor Kokoro en {self.api_url}...")
        start_time = time.time()
        while time.time() - start_time < max_wait:
            if self.is_server_running(timeout=2.0):
                logger.info("Servidor Kokoro conectado.")
                return True
            if callback:
                elapsed = int(time.time() - start_time)
                callback(f"Esperando servidor Kokoro... ({elapsed}s)")
            time.sleep(2)
        logger.error(f"Timeout esperando servidor Kokoro después de {max_wait}s")
        return False

    def get_available_voices(self) -> list[str]:
        """Devuelve la lista de voces disponibles para Kokoro desde voices.json."""
        return list(self.voice_manager.get_voices_for_language("kokoro", "es").keys())

    def get_voice_language_code(self, voice_id: str) -> str:
        """Obtiene el código de idioma para una voz específica (e.g., 'e' para español)."""
        return self.voice_manager.get_voice_code_for_language("kokoro", voice_id) or 'e'

    def generate_audio(
        self,
        text: str,
        voice: str,
        output_path: str | None = None,
        speed: float = 1.0,
        response_format: str = "mp3",
        callback: Callable[[bool, str], None] | None = None
    ) -> str | None:
        """
        Genera audio usando la API de Kokoro.
        
        Args:
            text: Texto a sintetizar.
            voice: ID de la voz (ej. 'ef_dora').
            output_path: Ruta donde guardar el audio. Si es None, se crea archivo temporal.
            speed: Velocidad de habla (0.5 - 2.0).
            response_format: Formato de salida ('mp3', 'wav', etc.)
            callback: Función llamada al finalizar: callback(success, message_or_path).
        
        Returns:
            Ruta del archivo generado si tiene éxito, None si falla.
        """
        self._cancel_event.clear()

        # Verificar servidor primero
        if not self.is_server_running(timeout=2.0):
            error_msg = f"Servidor Kokoro no está corriendo en {self.api_url}. Inícialo con:\n" \
                        "docker run -d -p 8880:8880 ghcr.io/remsky/kokoro-fastapi-cpu:latest"
            logger.error(error_msg)
            if callback:
                callback(False, error_msg)
            return None

        # Obtener código de idioma
        lang_code = self.get_voice_language_code(voice)

        # Preparar payload según la API de Kokoro-FastAPI
        payload = {
            "input": text,
            "voice": voice,
            "lang_code": lang_code,
            "response_format": response_format,
            "speed": speed
        }

        # Si no se especifica output_path, crear uno temporal
        if output_path is None:
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{response_format}")
            output_path = temp_file.name
            temp_file.close()

        try:
            # Realizar solicitud POST con streaming
            response = requests.post(
                f"{self.api_url}/v1/audio/speech",
                json=payload,
                timeout=120,
                stream=True
            )

            if response.status_code == 200:
                # Escribir el audio en chunks, verificando cancelación
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if self._cancel_event.is_set():
                            f.close()
                            if os.path.exists(output_path):
                                os.remove(output_path)
                            if callback:
                                callback(False, "Generación cancelada por el usuario")
                            return None
                        if chunk:
                            f.write(chunk)

                logger.info(f"Audio local generado: {output_path} (voz: {voice}, idioma: {lang_code})")
                if callback:
                    callback(True, output_path)
                return output_path
            else:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get("detail", response.text)
                except Exception as e:
                    logger.debug(f"No se pudo parsear JSON de error: {e}")
                error_msg = f"Error Kokoro {response.status_code}: {error_detail}"
                logger.error(error_msg)
                if callback:
                    callback(False, error_msg)
                return None

        except requests.exceptions.ConnectionError as e:
            error_msg = f"No se pudo conectar al servidor Kokoro: {e}"
            logger.error(error_msg)
            if callback:
                callback(False, error_msg)
            return None
        except Exception as e:
            error_msg = f"Error en TTS local: {str(e)}"
            logger.error(error_msg)
            if callback:
                callback(False, error_msg)
            return None

    def cancel(self):
        """Cancela la generación en curso."""
        self._cancel_event.set()
