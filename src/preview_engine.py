# src/preview_engine.py
import logging
from PIL import Image
import threading

logger = logging.getLogger("Narrivox")

try:
    from moviepy import VideoFileClip, ImageClip, AudioFileClip, CompositeVideoClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

class PreviewEngine:
    """Motor encargado de generar frames de previsualización para la UI."""
    def __init__(self, config: dict):
        self.config = config
        self.current_composition = None
        self._lock = threading.Lock()

    def update_composition(self, visual_clips, audio_clips, duration):
        """Crea una composición ligera de MoviePy para previsualizar."""
        if not MOVIEPY_AVAILABLE:
            return
        
        with self._lock:
            try:
                # clips visuales: lista de dict {path, start, end, type}
                mv_clips = []
                for c in visual_clips:
                    if not os.path.exists(c['path']):
                        continue
                        
                    if c['type'] == 'image':
                        clip = ImageClip(c['path']).with_start(c['start']).with_duration(c['end'] - c['start'])
                        mv_clips.append(clip)
                    elif c['type'] == 'video':
                        clip = VideoFileClip(c['path']).with_start(c['start']).subclipped(0, c['end'] - c['start'])
                        mv_clips.append(clip)
                
                if mv_clips:
                    self.current_composition = CompositeVideoClip(mv_clips, size=(640, 360))
                    self.current_composition.duration = duration
                    logger.info("Composición de preview actualizada")
                else:
                    self.current_composition = None
            except Exception as e:
                logger.error(f"Error creando composición de preview: {e}")

    def get_frame(self, t):
        """Obtiene un frame en el tiempo t como una imagen PIL."""
        if not self.current_composition:
            return None
        
        try:
            # Asegurarse de que t no exceda la duración
            t = min(t, self.current_composition.duration - 0.1)
            if t < 0: t = 0
            frame = self.current_composition.get_frame(t)
            return Image.fromarray(frame)
        except Exception as e:
            logger.error(f"Error obteniendo frame en t={t}: {e}")
            return None

    def close(self):
        if self.current_composition:
            try:
                self.current_composition.close()
            except Exception:
                pass
import os
