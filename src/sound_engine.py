# src/sound_engine.py
import os
import secrets
import sys
import traceback

from src.utils import logger

try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except Exception as exc:
    # FFmpeg es opcional al arrancar; las funciones de audio informarán si falta.
    static_ffmpeg = None
    logger.warning("FFmpeg estático no disponible: %s", exc)

# --- BLOQUE DE IMPORTACIÓN DE PYDUB ---
try:
    import pydub
    from pydub import AudioSegment
    from pydub.effects import normalize
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logger.warning("Pydub no encontrado.")
except Exception as e:
    # Ignorar errores de 'audioop' en Python 3.13+ si Pydub funciona sin él
    if "audioop" in str(e):
        PYDUB_AVAILABLE = True
        logger.info("Pydub cargado (audioop no soportado en Python 3.13, continuando de todos modos).")
    else:
        PYDUB_AVAILABLE = False
        logger.error(f"Error crítico cargando Pydub: {e}")
# -------------------------------------


class SoundtrackSelector:
    def __init__(self, config: dict):
        self.config = config
        self.music_base = os.path.join(config.get("base_folder", os.getcwd()), "assets", "music")
        self.emotion_map = {
            "Miedo": "Terror", "Terror": "Terror", "Ansiedad": "Terror", "Pavor": "Terror",
            "Épico": "Épico", "Fantasía Épica": "Épico", "Alegría": "Épico",
            "Sci-Fi": "Sci-Fi", "Cyberpunk": "Sci-Fi",
            "Misterio": "Misterio", "Suspenso": "Misterio", "Curiosidad": "Misterio",
            "Drama": "Drama", "Tristeza": "Drama",
            "Acción": "Acción", "Crimen": "Acción", "Ira": "Acción"
        }

    def get_music_for_emotion(self, emotion: str) -> str | None:
        if not PYDUB_AVAILABLE:
            return None
        category = self.emotion_map.get(emotion, "Misterio")
        folder = os.path.join(self.music_base, category)
        if not os.path.isdir(folder):
            logger.warning(f"Carpeta de música no encontrada: {folder}")
            return None
        files = [f for f in os.listdir(folder) if f.lower().endswith(('.mp3', '.wav', '.ogg'))]
        if not files:
            logger.warning(f"No hay archivos de música en {folder}")
            return None
        return os.path.join(folder, secrets.SystemRandom().choice(files))


class SoundMixer:
    def __init__(self, config: dict):
        self.config = config
        self.music_volume = config.get("music_volume", 0.15)
        self.ducking_enabled = config.get("ducking_enabled", True)
        self.ducking_attenuation = config.get("ducking_attenuation", -10)

    def mix(
        self,
        narration_path: str,
        music_path: str | None = None,
        sfx_paths: list[str] = None,
        output_path: str = None
    ) -> str | None:
        if not PYDUB_AVAILABLE:
            logger.error("Pydub no disponible, no se puede mezclar audio.")
            return None

        try:
            narration = AudioSegment.from_file(narration_path)
            narration = normalize(narration)
            mixed = narration

            if music_path and os.path.exists(music_path):
                music = AudioSegment.from_file(music_path)
                music = music - (20 * (1 - self.music_volume))
                if len(music) < len(narration):
                    music = music * (len(narration) // len(music) + 1)
                music = music[:len(narration)]
                if self.ducking_enabled:
                    music = music - abs(self.ducking_attenuation)
                mixed = mixed.overlay(music)

            if sfx_paths:
                for sfx_path in sfx_paths:
                    if os.path.exists(sfx_path):
                        sfx = AudioSegment.from_file(sfx_path)
                        sfx = sfx - 5
                        mixed = mixed.overlay(sfx)

            if output_path is None:
                output_path = narration_path.replace(".mp3", "_mixed.mp3")
            mixed.export(output_path, format="mp3")
            logger.info(f"Audio mezclado guardado en: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error mezclando audio: {e}")
            return None


class SoundEngine:
    def __init__(self, config: dict):
        self.config = config
        self.selector = SoundtrackSelector(config)
        self.mixer = SoundMixer(config)

    def generate_soundtrack(
        self,
        narration_path: str,
        emotion: str,
        output_path: str | None = None,
        sfx_paths: list[str] = None
    ) -> str | None:
        music_path = self.selector.get_music_for_emotion(emotion)
        if not music_path:
            logger.warning(f"No se encontró música para emoción '{emotion}'. Usando solo narración.")
        return self.mixer.mix(narration_path, music_path, sfx_paths, output_path)
