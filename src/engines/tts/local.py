import logging
import threading
from src.engines.tts.base import BaseTTSEngine
from src.exceptions import AudioGenerationError
from src.local_tts_engine import LocalTTSEngine as KokoroEngine
from src.voice_manager import VoiceManager

logger = logging.getLogger("Narrivox")

class LocalTTSEngine(BaseTTSEngine):
    def __init__(self, config: dict):
        super().__init__(config)
        self.local_engine = KokoroEngine(config)
        self.voice_manager = VoiceManager()
        self.all_voices = {}
        self.voices_by_language = {"Todos": {}}
        self.voice_names = []

    def load_voices(self, on_loaded_callback=None):
        voices_dict = self.voice_manager.get_all_voices_flat("kokoro")
        self.all_voices = voices_dict
        self.voice_names = list(voices_dict.keys())
        self.voices_by_language = {"Todos": voices_dict}
        
        languages = self.voice_manager.get_languages("kokoro")
        for lang_code, lang_data in languages.items():
            lang_name = lang_data["name"]
            self.voices_by_language[lang_name] = {}
            for variant, variant_data in lang_data.get("variants", {}).items():
                self.voices_by_language[lang_name].update(variant_data.get("voices", {}))
        
        logger.info(f"Voces locales (Kokoro) cargadas: {len(self.voice_names)} voces")
        if on_loaded_callback:
            on_loaded_callback()

    def generate_audio(self, text: str, output_path: str, voice_code: str) -> str:
        if not self.local_engine.is_server_running():
            raise AudioGenerationError(
                "Servidor Kokoro no está disponible. Asegúrate de que esté corriendo en http://localhost:8880"
            )

        success = [False]
        error_msg = [""]
        event = threading.Event()

        def callback(ok, msg):
            success[0] = ok
            error_msg[0] = msg if not ok else ""
            event.set()

        self.local_engine.generate_audio(text, voice_code, output_path, callback=callback)
        event.wait(timeout=120)

        if not success[0]:
            raise AudioGenerationError(f"Error TTS local: {error_msg[0]}")
            
        return self._generate_synthetic_srt(text, output_path)
