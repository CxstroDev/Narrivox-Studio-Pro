import logging
from src.engines.video.subtitles import SubtitleManager

logger = logging.getLogger("Narrivox")

try:
    from moviepy import AudioFileClip, CompositeVideoClip, ImageClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

class VideoComposer:
    @staticmethod
    def compose(image_path: str, audio_path: str, srt_path: str, output_path: str, height=720):
        if not MOVIEPY_AVAILABLE:
            logger.error("MoviePy no disponible para composición.")
            return False

        audio_clip = None
        img_clip = None
        video = None
        subs = None

        try:
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration

            img_clip = ImageClip(image_path).with_duration(duration)
            img_clip = img_clip.resized(height=height)

            subs = SubtitleManager.create_subtitles(srt_path, img_clip.w)
            
            clips = [img_clip]
            if subs:
                clips.append(subs)

            video = CompositeVideoClip(clips)
            video = video.with_audio(audio_clip)

            video.write_videofile(
                output_path,
                fps=24,
                codec='libx264',
                audio_codec='aac',
                verbose=False,
                logger=None
            )
            return True

        except Exception as e:
            logger.error(f"Error en composición de video: {e}")
            return False
        finally:
            if audio_clip: audio_clip.close()
            if img_clip: img_clip.close()
            if video: video.close()
