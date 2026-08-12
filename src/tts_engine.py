import asyncio
import logging
import os
import threading
import pygame

from src.exceptions import AudioGenerationError
from src.engines.tts.edge import EdgeTTSEngine
from src.engines.tts.elevenlabs import ElevenLabsTTSEngine
from src.engines.tts.unrealspeech import UnrealSpeechTTSEngine
from src.engines.tts.local import LocalTTSEngine

logger = logging.getLogger("Narrivox")

class TTSEngine:
    def __init__(self, config: dict):
        self.config = config
        self.provider = config.get("tts_provider", "edge")
        pygame.mixer.init()
        self.temp_file = "temp_preview.mp3"
        self.loop = None
        self._loop_thread = None
        self._start_loop()

        self.on_voices_loaded = None
        self._cancel_event = threading.Event()
        self._current_task_thread = None

        # Factory initialization
        self.engine = self._create_engine()
        self.engine.load_voices(on_loaded_callback=self._handle_voices_loaded)

    def _create_engine(self):
        if self.provider == "edge":
            return EdgeTTSEngine(self.config, loop=self.loop)
        elif self.provider == "elevenlabs":
            return ElevenLabsTTSEngine(self.config)
        elif self.provider == "unrealspeech":
            return UnrealSpeechTTSEngine(self.config)
        elif self.provider == "local":
            return LocalTTSEngine(self.config)
        else:
            logger.warning(f"Proveedor {self.provider} desconocido, usando Edge como fallback.")
            return EdgeTTSEngine(self.config, loop=self.loop)

    def _handle_voices_loaded(self):
        if self.on_voices_loaded:
            self._run_in_main_thread(self.on_voices_loaded)

    def _start_loop(self):
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        self._loop_thread = threading.Thread(target=run_loop, daemon=True)
        self._loop_thread.start()
        while self.loop is None:
            pass

    @property
    def all_voices(self):
        return self.engine.all_voices

    @property
    def voices_by_language(self):
        return self.engine.voices_by_language

    @property
    def voice_names(self):
        return self.engine.voice_names

    def get_filtered_voices(self, language_filter="Todos"):
        if language_filter in self.voices_by_language:
            return self.voices_by_language[language_filter]
        return self.all_voices

    def get_language_filters(self):
        if self.voices_by_language:
            return list(self.voices_by_language.keys())
        return ["Todos", "Español", "Inglés"]

    def get_voice_code(self, display_name, language_filter="Todos"):
        if self.provider == "local":
            return display_name
        voices_dict = self.get_filtered_voices(language_filter)
        code = voices_dict.get(display_name)
        if not code:
            code = self.all_voices.get(display_name)
        if not code:
            code = display_name
        return code

    def generate_audio(self, text: str, output_path: str, voice_code: str) -> str:
        self._cancel_event.clear()
        try:
            # Pass cancel_event only if supported (Edge)
            if isinstance(self.engine, EdgeTTSEngine):
                srt_content = self.engine.generate_audio(text, output_path, voice_code, cancel_event=self._cancel_event)
            else:
                srt_content = self.engine.generate_audio(text, output_path, voice_code)
            
            if self._cancel_event.is_set():
                return ""
            return srt_content
        except Exception as e:
            logger.warning(f"Fallo con {self.provider}: {e}. Usando fallback Edge.")
            if self.provider != "edge":
                fallback_engine = EdgeTTSEngine(self.config, loop=self.loop)
                return fallback_engine.generate_audio(text, output_path, "es-MX-JorgeNeural")
            raise AudioGenerationError(f"Error crítico en TTS: {e}")

    def play_preview(self, text: str, voice_code: str, on_ready_callback=None):
        self._cancel_event.clear()

        def task():
            try:
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()
                pygame.mixer.music.unload()

                if self._cancel_event.is_set():
                    return

                # Generar preview usando el motor actual
                if isinstance(self.engine, EdgeTTSEngine):
                    self.engine.generate_audio(text, self.temp_file, voice_code, cancel_event=self._cancel_event)
                else:
                    self.engine.generate_audio(text, self.temp_file, voice_code)

                if self._cancel_event.is_set():
                    return

                if on_ready_callback:
                    self._run_in_main_thread(on_ready_callback)

                if os.path.exists(self.temp_file):
                    pygame.mixer.music.load(self.temp_file)
                    pygame.mixer.music.play()
            except Exception as e:
                logger.error(f"Error en preview: {e}")

        self._current_task_thread = threading.Thread(target=task, daemon=True)
        self._current_task_thread.start()

    def _run_in_main_thread(self, func, *args, **kwargs):
        try:
            import tkinter as tk
            root = tk._default_root
            if root:
                root.after(0, lambda: func(*args, **kwargs))
            else:
                func(*args, **kwargs)
        except Exception as e:
            logger.debug(f"Error ejecutando en hilo principal: {e}")
            try:
                func(*args, **kwargs)
            except Exception as e2:
                logger.debug(f"Error ejecutando callback directamente: {e2}")

    def stop_audio(self):
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()

    def cancel_audio(self):
        self._cancel_event.set()
        if self._current_task_thread and self._current_task_thread.is_alive():
            self._current_task_thread.join(timeout=0.5)
            self._current_task_thread = None
        self.stop_audio()
        logger.info("Cancelación de audio solicitada")
