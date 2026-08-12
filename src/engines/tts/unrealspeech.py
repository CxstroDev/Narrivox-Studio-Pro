import logging
import os
import requests
from src.engines.tts.base import BaseTTSEngine
from src.exceptions import AudioGenerationError

logger = logging.getLogger("Narrivox")

class UnrealSpeechTTSEngine(BaseTTSEngine):
    CHAR_LIMIT = 1000

    def __init__(self, config: dict):
        super().__init__(config)
        self.all_voices = {}
        self.voices_by_language = {"Todos": {}}
        self.voice_names = []

    def load_voices(self, on_loaded_callback=None):
        self.all_voices = {
            "Scarlett (Femenina, US)": "Scarlett",
            "Dan (Masculino, US)": "Dan",
            "Liv (Femenina, UK)": "Liv",
            "Will (Masculino, UK)": "Will",
            "Amy (Femenina, US)": "Amy",
        }
        self.voices_by_language = {
            "Todos": self.all_voices,
            "Inglés": self.all_voices.copy(),
            "Español": {},
        }
        self.voice_names = list(self.all_voices.keys())
        if on_loaded_callback:
            on_loaded_callback()

    def generate_audio(self, text: str, output_path: str, voice_code: str) -> str:
        api_key = self.config.get("unrealspeech_api_key", "")
        if not api_key:
            raise AudioGenerationError("Falta API Key de Unreal Speech")
        
        chunks = self._chunk_text(text, self.CHAR_LIMIT)

        if len(chunks) == 1:
            self._generate_single(text, output_path, voice_code, api_key)
        else:
            temp_files = []
            try:
                for i, chunk in enumerate(chunks):
                    temp_file = f"{output_path}.part{i}.mp3"
                    self._generate_single(chunk, temp_file, voice_code, api_key)
                    temp_files.append(temp_file)
                self._concatenate_audio_files(temp_files, output_path)
                logger.info(f"Audio UnrealSpeech concatenado desde {len(chunks)} partes: {output_path}")
            finally:
                for tf in temp_files:
                    if os.path.exists(tf):
                        os.remove(tf)
        
        return self._generate_synthetic_srt(text, output_path)

    def _generate_single(self, text: str, output_path: str, voice_id: str, api_key: str):
        url = "https://api.v7.unrealspeech.com/speech"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "Text": text,
            "VoiceId": voice_id,
            "Bitrate": "192k",
            "Speed": "0",
            "Pitch": "1",
            "TimestampType": "sentence"
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            if response.status_code == 200:
                data = response.json()
                audio_url = data.get("OutputUri")
                if audio_url:
                    audio_resp = requests.get(audio_url, timeout=30)
                    with open(output_path, "wb") as f:
                        f.write(audio_resp.content)
                    logger.info(f"Audio Unreal Speech generado: {output_path}")
                else:
                    raise AudioGenerationError("No se recibió URL de audio")
            else:
                raise AudioGenerationError(f"Unreal Speech error {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Error Unreal Speech: {e}")
            raise AudioGenerationError(f"Fallo Unreal Speech: {e}")
