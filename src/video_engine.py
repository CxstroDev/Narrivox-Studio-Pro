import logging
from src.engines.video.composer import VideoComposer

logger = logging.getLogger("Narrivox")

try:
    import moviepy
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    logger.warning("moviepy no está instalado. La funcionalidad de video no estará disponible.")

class VideoEngine:
    def __init__(self, config: dict):
        self.config = config
        if not MOVIEPY_AVAILABLE:
            logger.error("VideoEngine inicializado pero moviepy no está instalado.")

    def assemble_video(self, image_path: str, audio_path: str, srt_path: str, output_path: str) -> bool:
        """
        Crea un video combinando imagen estática, audio y subtítulos.
        Retorna True si tiene éxito, False en caso de error.
        """
        if not MOVIEPY_AVAILABLE:
            logger.error("No se puede ensamblar video: moviepy no está instalado.")
            return False

        return VideoComposer.compose(image_path, audio_path, srt_path, output_path)
