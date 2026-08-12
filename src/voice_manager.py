# src/voice_manager.py
import json
from pathlib import Path


class VoiceManager:
    def __init__(self):
        self.voices_data = self._load_voices()

    def _load_voices(self) -> dict:
        voices_path = Path(__file__).parent / "voices.json"
        try:
            with open(voices_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando voices.json: {e}")
            return {}

    def get_providers(self) -> list[str]:
        return list(self.voices_data.keys())

    def get_provider_name(self, provider: str) -> str:
        return self.voices_data.get(provider, {}).get("name", provider)

    def get_languages(self, provider: str) -> dict[str, dict]:
        return self.voices_data.get(provider, {}).get("languages", {})

    def get_language_list(self, provider: str) -> list[dict[str, str]]:
        languages = self.get_languages(provider)
        seen = set()
        result = []
        for code, data in languages.items():
            base_code = code.split('-')[0]
            if base_code not in seen:
                seen.add(base_code)
                base_name = self._get_base_language_name(base_code)
                result.append({"code": base_code, "name": base_name})
        return result

    def _get_base_language_name(self, code: str) -> str:
        names = {
            "es": "Español",
            "en": "Inglés",
            "fr": "Francés",
            "de": "Alemán",
            "it": "Italiano",
            "pt": "Portugués",
            "ja": "Japonés",
            "zh": "Chino",
            "hi": "Hindi",
            "ar": "Árabe",
            "ru": "Ruso"
        }
        return names.get(code, code.upper())

    def get_voices_for_language(self, provider: str, lang_code: str) -> dict[str, str]:
        languages = self.get_languages(provider)
        voices = {}
        for code, lang_data in languages.items():
            if code.startswith(lang_code):
                for variant, variant_data in lang_data.get("variants", {}).items():
                    voices.update(variant_data.get("voices", {}))
        return voices

    def get_all_voices_flat(self, provider: str) -> dict[str, str]:
        languages = self.get_languages(provider)
        all_voices = {}
        for lang_code, lang_data in languages.items():
            for variant, variant_data in lang_data.get("variants", {}).items():
                all_voices.update(variant_data.get("voices", {}))
        return all_voices

    def get_voice_display_name(self, provider: str, voice_id: str) -> str:
        all_voices = self.get_all_voices_flat(provider)
        return all_voices.get(voice_id, voice_id)

    def get_voice_code_for_language(self, provider: str, voice_id: str) -> str | None:
        languages = self.get_languages(provider)
        for lang_code, lang_data in languages.items():
            for variant, variant_data in lang_data.get("variants", {}).items():
                if voice_id in variant_data.get("voices", {}):
                    return lang_data.get("code", lang_code)
        return None
