import logging
import threading
import os
import requests
from src.engines.tts.base import BaseTTSEngine
from src.exceptions import AudioGenerationError

logger = logging.getLogger("Narrivox")

try:
    from elevenlabs.client import ElevenLabs
    ELEVENLABS_SDK_AVAILABLE = True
except ImportError:
    ELEVENLABS_SDK_AVAILABLE = False

class ElevenLabsTTSEngine(BaseTTSEngine):
    CHAR_LIMIT = 5000

    def __init__(self, config: dict):
        super().__init__(config)
        self.all_voices = {}
        self.voices_by_language = {"Todos": {}}
        self.voice_names = []

    def load_voices(self, on_loaded_callback=None):
        api_key = self.config.get("elevenlabs_api_key", "").strip()
        if not api_key:
            logger.warning("No se ha configurado API Key de ElevenLabs. Usando lista de voces de respaldo.")
            self._use_fallback_voices()
            if on_loaded_callback:
                on_loaded_callback()
            return

        def fetch_voices():
            try:
                url = "https://api.elevenlabs.io/v1/voices"
                headers = {"xi-api-key": api_key}
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                voices_data = response.json().get("voices", [])

                spanish_friendly_ids = {
                    "7QQzpAyzlKTVrRzQJmTE", "usTmJvQOCyW3nRcZ8OEo", "zl1Ut8dvwcVSuQSB9XkG",
                    "pNInz6obpgDQGcFmaJgB", "VR6AewLTigWG4xSOukaG", "jBpfuIE2acCO8z3wKNLl",
                    "zcAOhNBS3c14rBihAFp1", "XrExE9yKIg1WjnnlVkGX", "EXAVITQu4vr4xnSDxMaL",
                    "pMsXgVXv3BLzUgSXRplE", "flq6f7yk4E4fJM5XTYuZ", "oWAxZDx7w5VEj9dCyTzz",
                    "21m00Tcm4TlvDq8ikWAM", "AZnzlk1XvdvUeBnXmlld", "ErXwobaYiN019PkySvjV",
                }

                all_voices = {}
                for voice in voices_data:
                    category = voice.get("category", "")
                    if category in ["professional"] and not voice.get("is_added_by_user", False):
                        continue
                    voice_id = voice["voice_id"]
                    name = voice.get("name", "Desconocido")
                    labels = voice.get("labels", {})
                    lang = labels.get("language", "").lower()

                    is_native_spanish = (lang == "es")
                    is_multilingual = ("multi" in lang) or (voice_id in spanish_friendly_ids)

                    if is_native_spanish:
                        display_lang = "Español"
                    elif is_multilingual:
                        display_lang = "Multilingüe"
                    else:
                        display_lang = lang.upper() if lang else "EN"

                    display_name = f"{name} ({display_lang})"
                    all_voices[display_name] = voice_id

                def sort_key(item):
                    name, _ = item
                    is_es = "Español" in name or "Multilingüe" in name
                    return (not is_es, name)

                sorted_voices = sorted(all_voices.items(), key=sort_key)
                self.all_voices = dict(sorted_voices)
                self.voices_by_language = {"Todos": self.all_voices}
                es_voices = {n: i for n, i in self.all_voices.items() if "Español" in n or "Multilingüe" in n}
                if es_voices:
                    self.voices_by_language["Español"] = es_voices
                self.voice_names = list(self.all_voices.keys())
                logger.info(f"Voces de ElevenLabs cargadas desde API: {len(self.voice_names)} voces")
                if on_loaded_callback:
                    on_loaded_callback()
            except Exception as e:
                logger.error(f"Error al cargar voces de ElevenLabs: {e}. Usando lista de respaldo.")
                self._use_fallback_voices()
                if on_loaded_callback:
                    on_loaded_callback()

        threading.Thread(target=fetch_voices, daemon=True).start()

    def _use_fallback_voices(self):
        self.all_voices = {
            "Dani (Español)": "7QQzpAyzlKTVrRzQJmTE",
            "Dante (Español)": "usTmJvQOCyW3nRcZ8OEo",
            "Ninoska (Español)": "zl1Ut8dvwcVSuQSB9XkG",
            "Lucía (Español)": "pNInz6obpgDQGcFmaJgB",
            "Mateo (Español)": "VR6AewLTigWG4xSOukaG",
            "Valentina (Español)": "jBpfuIE2acCO8z3wKNLl",
            "Santiago (Español)": "zcAOhNBS3c14rBihAFp1",
            "Camila (Español)": "XrExE9yKIg1WjnnlVkGX",
            "Emily (Multilingüe)": "EXAVITQu4vr4xnSDxMaL",
            "Serena (Multilingüe)": "pMsXgVXv3BLzUgSXRplE",
            "Michael (Multilingüe)": "flq6f7yk4E4fJM5XTYuZ",
            "Grace (Multilingüe)": "oWAxZDx7w5VEj9dCyTzz",
            "Rachel (Multilingüe)": "21m00Tcm4TlvDq8ikWAM",
            "Antoni (Multilingüe)": "ErXwobaYiN019PkySvjV",
        }
        self.voices_by_language = {
            "Todos": self.all_voices,
            "Español": {k: v for k, v in self.all_voices.items() if "Español" in k or "Multilingüe" in k},
            "Inglés": {k: v for k, v in self.all_voices.items() if "(US)" in k or "(UK)" in k},
        }
        self.voice_names = list(self.all_voices.keys())

    def generate_audio(self, text: str, output_path: str, voice_code: str) -> str:
        api_key = self.config.get("elevenlabs_api_key", "")
        if not api_key:
            raise AudioGenerationError("Falta API Key de ElevenLabs")

        model_id = self.config.get("elevenlabs_model_id", "eleven_multilingual_v2")
        chunks = self._chunk_text(text, self.CHAR_LIMIT)

        if len(chunks) == 1:
            self._generate_single(text, output_path, voice_code, api_key, model_id)
        else:
            temp_files = []
            try:
                for i, chunk in enumerate(chunks):
                    temp_file = f"{output_path}.part{i}.mp3"
                    self._generate_single(chunk, temp_file, voice_code, api_key, model_id)
                    temp_files.append(temp_file)
                self._concatenate_audio_files(temp_files, output_path)
                logger.info(f"Audio ElevenLabs concatenado desde {len(chunks)} partes: {output_path}")
            finally:
                for tf in temp_files:
                    if os.path.exists(tf):
                        os.remove(tf)
        
        return self._generate_synthetic_srt(text, output_path)

    def _generate_single(self, text: str, output_path: str, voice_id: str, api_key: str, model_id: str):
        if ELEVENLABS_SDK_AVAILABLE:
            try:
                client = ElevenLabs(api_key=api_key)
                audio_iter = client.text_to_speech.convert(
                    text=text,
                    voice_id=voice_id,
                    model_id=model_id,
                    output_format="mp3_44100_128"
                )
                audio_bytes = b"".join(audio_iter)
                with open(output_path, "wb") as f:
                    f.write(audio_bytes)
                logger.info(f"Audio ElevenLabs generado con SDK: {output_path}")
            except Exception as e:
                logger.error(f"Error ElevenLabs SDK: {e}")
                self._generate_single_requests(text, output_path, voice_id, api_key, model_id)
        else:
            self._generate_single_requests(text, output_path, voice_id, api_key, model_id)

    def _generate_single_requests(self, text: str, output_path: str, voice_id: str, api_key: str, model_id: str):
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        data = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
        }
        try:
            response = requests.post(url, json=data, headers=headers, timeout=60)
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                logger.info(f"Audio ElevenLabs generado con requests: {output_path}")
            elif response.status_code == 402:
                raise AudioGenerationError(
                    "Error 402: Tu plan de ElevenLabs no permite usar esta voz. "
                    "Por favor, selecciona una voz gratuita o actualiza tu plan."
                )
            else:
                raise AudioGenerationError(f"ElevenLabs error {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Error ElevenLabs: {e}")
            raise AudioGenerationError(f"Fallo ElevenLabs: {e}")
