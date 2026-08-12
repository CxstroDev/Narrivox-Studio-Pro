import logging

logger = logging.getLogger("Narrivox")

try:
    from moviepy import TextClip
    from moviepy.video.tools.subtitles import SubtitlesClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

class SubtitleManager:
    @staticmethod
    def create_subtitles(srt_path: str, video_width: int):
        if not MOVIEPY_AVAILABLE:
            return None

        def subtitle_generator(txt):
            return TextClip(
                txt,
                font='Arial',
                fontsize=32,
                color='white',
                stroke_color='black',
                stroke_width=2,
                method='caption',
                size=(int(video_width * 0.9), None)
            )

        try:
            subs = SubtitlesClip(srt_path, subtitle_generator)
            return subs.with_position(('center', 'bottom'))
        except Exception as e:
            logger.error(f"Error creando subtítulos: {e}")
            return None
