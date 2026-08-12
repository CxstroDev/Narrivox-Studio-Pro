# src/cinematic_engine.py
import os
import shutil
from urllib.parse import urlparse

import requests

from src.utils import logger

try:
    from moviepy import (
        AudioFileClip,
        CompositeVideoClip,
        ImageClip,
        TextClip,
        VideoClip,
        VideoFileClip,
        concatenate_videoclips,
    )
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    logger.warning("MoviePy no está instalado. Motor Cinemático no funcionará.")

try:
    from gradio_client import Client, handle_file
    GRADIO_AVAILABLE = True
except ImportError:
    GRADIO_AVAILABLE = False
    logger.warning("gradio_client no instalado. Helios y SVD no estarán disponibles.")


class KenBurnsEffect:
    @staticmethod
    def apply(clip: ImageClip, zoom_factor: float = 1.1, duration: float | None = None) -> VideoClip:
        if duration is None:
            duration = clip.duration

        def make_frame(t):
            progress = t / duration
            current_zoom = 1.0 + (zoom_factor - 1.0) * progress
            new_w = int(clip.w * current_zoom)
            new_h = int(clip.h * current_zoom)
            resized = clip.resized(new_size=(new_w, new_h))
            return resized.get_frame(t)

        return VideoClip(make_frame, duration=duration).with_audio(clip.audio)


class BRollIntegrator:
    """Busca e integra clips de B‑Roll desde Pexels o Pixabay."""

    def __init__(self, config: dict):
        self.config = config
        self.provider = config.get("broll_provider", "pexels")
        self.api_key = config.get("pexels_api_key", "") if self.provider == "pexels" else config.get("pixabay_api_key", "")
        self.cache_dir = os.path.join(config.get("base_folder", os.getcwd()), "broll_cache")
        os.makedirs(self.cache_dir, exist_ok=True)

    def extract_keywords(self, script: str, max_keywords: int = 3) -> list[str]:
        import re
        from collections import Counter
        words = re.findall(r'\b[a-zA-ZáéíóúÁÉÍÓÚñÑ]{5,}\b', script.lower())
        stopwords = {'sobre', 'desde', 'hacia', 'hasta', 'entre', 'para', 'como', 'mismo', 'todos'}
        filtered = [w for w in words if w not in stopwords]
        counter = Counter(filtered)
        return [word for word, _ in counter.most_common(max_keywords)]

    def search_videos(self, keyword: str, per_page: int = 5) -> list[str]:
        if not self.api_key:
            return []
        try:
            if self.provider == "pexels":
                return self._search_pexels(keyword, per_page)
            elif self.provider == "pixabay":
                return self._search_pixabay(keyword, per_page)
        except Exception as e:
            logger.error(f"Error buscando videos: {e}")
        return []

    def _search_pexels(self, keyword: str, per_page: int) -> list[str]:
        headers = {"Authorization": self.api_key}
        params = {"query": keyword, "per_page": per_page}
        resp = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        urls = []
        for video in data.get("videos", []):
            files = video.get("video_files", [])
            if files:
                file_info = next((f for f in files if f.get("quality") == "sd"), files[0])
                urls.append(file_info["link"])
        return urls

    def _search_pixabay(self, keyword: str, per_page: int) -> list[str]:
        params = {"key": self.api_key, "q": keyword, "video_type": "film", "per_page": per_page}
        resp = requests.get("https://pixabay.com/api/videos/", params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        urls = []
        for hit in data.get("hits", []):
            videos = hit.get("videos", {})
            for quality in ["medium", "large", "small"]:
                if quality in videos:
                    urls.append(videos[quality]["url"])
                    break
        return urls

    def download_video(self, url: str) -> str | None:
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path) or f"broll_{hash(url)}.mp4"
        local_path = os.path.join(self.cache_dir, filename)
        if os.path.exists(local_path):
            return local_path
        try:
            resp = requests.get(url, stream=True, timeout=30)
            resp.raise_for_status()
            with open(local_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"B‑Roll descargado: {local_path}")
            return local_path
        except Exception as e:
            logger.error(f"Error descargando B‑Roll {url}: {e}")
            return None

    def get_broll_clips(self, script: str, max_duration: float = 5.0) -> list[VideoFileClip]:
        if not MOVIEPY_AVAILABLE:
            return []
        keywords = self.extract_keywords(script)
        all_urls = []
        for kw in keywords:
            urls = self.search_videos(kw)
            all_urls.extend(urls[:2])
            if len(all_urls) >= 5:
                break
        clips = []
        for url in all_urls[:5]:
            local = self.download_video(url)
            if local:
                try:
                    clip = VideoFileClip(local).without_audio()
                    if clip.duration > max_duration:
                        clip = clip.subclipped(0, max_duration)
                    clips.append(clip)
                except Exception as e:
                    logger.error(f"Error cargando clip {local}: {e}")
        return clips


class StyledSubtitles:
    """Genera subtítulos estilizados con fondo semitransparente."""

    def __init__(self, font: str = "Arial", fontsize: int = 32,
                 color: str = "white", stroke_color: str = "black", stroke_width: int = 2,
                 bg_color: tuple[int, int, int, int] = (0, 0, 0, 128)):
        self.font = font
        self.fontsize = fontsize
        self.color = color
        self.stroke_color = stroke_color
        self.stroke_width = stroke_width
        self.bg_color = bg_color

    def create_subtitle_clip(self, txt: str, duration: float, video_width: int) -> TextClip:
        txt_clip = TextClip(
            text=txt,
            font=self.font,
            font_size=self.fontsize,
            color=self.color,
            stroke_color=self.stroke_color,
            stroke_width=self.stroke_width,
            method='caption',
            size=(int(video_width * 0.9), None)
        ).with_duration(duration)

        bg_clip = TextClip(
            text=txt,
            font=self.font,
            font_size=self.fontsize,
            color='black',
            bg_color=self.bg_color,
            method='caption',
            size=(int(video_width * 0.9), None)
        ).with_duration(duration)

        return CompositeVideoClip([bg_clip, txt_clip]).crossfadein(0.2)

    def parse_srt(self, srt_path: str, video_width: int) -> list[TextClip]:
        from moviepy.video.tools.subtitles import SubtitlesClip
        generator = lambda txt: self.create_subtitle_clip(txt, 1, video_width)
        return SubtitlesClip(srt_path, generator)


class CinematicEngine:
    def __init__(self, config: dict):
        self.config = config
        self.broll = BRollIntegrator(config) if config.get("enable_broll", False) else None
        self.subs = StyledSubtitles()

    @staticmethod
    def _close_video_clips(*clips) -> None:
        """Cierra clips MoviePy sin fallar durante la limpieza."""
        closed = set()
        for clip in clips:
            if clip is None or id(clip) in closed:
                continue
            closed.add(id(clip))
            close = getattr(clip, "close", None)
            if callable(close):
                try:
                    close()
                except Exception as exc:
                    logger.debug("No se pudo cerrar un clip: %s", exc)

    @staticmethod
    def _cleanup_temporary_files(output_path: str) -> None:
        """Elimina únicamente los temporales generados junto al video de salida."""
        base, _ = os.path.splitext(output_path)
        for temp_path in (f"{base}_helios_temp.mp4", f"{base}_svd_temp.mp4"):
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except OSError as exc:
                logger.debug("No se pudo eliminar temporal %s: %s", temp_path, exc)

    def _generate_helios_video(self, image_path: str, prompt: str, output_path: str, duration: float = 5.0) -> bool:
        if not GRADIO_AVAILABLE:
            return False
        try:
            space = self.config.get("helios_space", "BestWishYsh/Helios-14B-RealTime-AOTI")
            client = Client(space)
            client.predict(mode="Image-to-Video", api_name="/update_conditional_visibility")
            fps = 24
            num_frames = min(int(duration * fps), 231)
            result = client.predict(
                mode="Image-to-Video",
                prompt=prompt,
                image_input=handle_file(image_path),
                video_input=handle_file(image_path),
                height=384,
                width=640,
                num_frames=float(num_frames),
                num_inference_steps=2.0,
                seed=42,
                is_amplify_first_chunk=True,
                api_name="/generate_video",
            )
            if isinstance(result, tuple) and len(result) > 0:
                generated_video_path = result[0]
                if os.path.exists(generated_video_path):
                    shutil.move(generated_video_path, output_path)
                    logger.info(f"Video generado con Helios: {output_path}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error en Helios: {e}")
            return False

    def _generate_svd_video(self, image_path: str, output_path: str, fps: int = 6, motion_bucket_id: int = 127) -> bool:
        if not GRADIO_AVAILABLE:
            return False
        try:
            space = self.config.get("svd_space", "fffiloni/stable-video-diffusion-img2vid")
            client = Client(space)
            result = client.predict(
                image=handle_file(image_path),
                seed=42,
                randomize_seed=True,
                decode_chunk_size=8,
                motion_bucket_id=motion_bucket_id,
                api_name="/predict"
            )
            if isinstance(result, str) and os.path.exists(result):
                shutil.move(result, output_path)
                logger.info(f"Video generado con SVD: {output_path}")
                return True
            elif isinstance(result, tuple) and len(result) > 0:
                video_path = result[0]
                if os.path.exists(video_path):
                    shutil.move(video_path, output_path)
                    return True
            return False
        except Exception as e:
            logger.error(f"Error en SVD: {e}")
            return False

    def _load_and_adjust_video_clip(self, video_path: str, target_duration: float) -> VideoFileClip | None:
        """Carga y ajusta un clip de video a la duración objetivo."""
        try:
            clip = VideoFileClip(video_path).without_audio()
            if clip.duration < target_duration:
                # Calcular cuántas veces necesitamos hacer loop
                n_loops = int(target_duration / clip.duration) + 1
                return clip.loop(n=n_loops).subclipped(0, target_duration)
            else:
                return clip.subclipped(0, target_duration)
        except Exception as e:
            logger.error(f"Error cargando video: {e}")
            return None

    def _generate_video_clip(self, base_image_path: str, script_text: str,
                            output_path: str, duration: float,
                            use_ken_burns: bool = True) -> VideoClip | None:
        """Genera un clip de video usando Helios, SVD o Ken Burns."""
        # 1. Intentar Helios
        if GRADIO_AVAILABLE:
            temp_helios = output_path.replace(".mp4", "_helios_temp.mp4")
            prompt = f"Realistic cinematic scene: {script_text[:200]}"
            if self._generate_helios_video(base_image_path, prompt, temp_helios, duration=duration):
                clip = self._load_and_adjust_video_clip(temp_helios, duration)
                if clip:
                    return clip

        # 2. Fallback a SVD
        if GRADIO_AVAILABLE:
            temp_svd = output_path.replace(".mp4", "_svd_temp.mp4")
            if self._generate_svd_video(base_image_path, temp_svd):
                clip = self._load_and_adjust_video_clip(temp_svd, duration)
                if clip:
                    return clip

        # 3. Fallback a Ken Burns
        img_clip = ImageClip(base_image_path).with_duration(duration)
        if use_ken_burns:
            return KenBurnsEffect.apply(img_clip, zoom_factor=1.1)
        else:
            return img_clip

    def _add_broll_if_enabled(self, video_clip: VideoClip, script_text: str) -> VideoClip:
        """Añade clips B-Roll si está habilitado."""
        if not (self.broll and script_text):
            return video_clip

        try:
            broll_clips = self.broll.get_broll_clips(script_text, max_duration=3.0)
            if broll_clips:
                return concatenate_videoclips([video_clip] + broll_clips)
        except Exception as e:
            logger.error(f"Error integrando B-Roll: {e}")

        return video_clip

    def _add_subtitles_if_enabled(self, video_clip: VideoClip, srt_path: str, style_params: dict = None) -> VideoClip:
        """Añade subtítulos si están disponibles con estilo personalizable."""
        if not (srt_path and os.path.exists(srt_path)):
            return video_clip

        try:
            if style_params:
                self.subs.font = style_params.get("font", self.subs.font)
                self.subs.fontsize = style_params.get("fontsize", self.subs.fontsize)
                self.subs.color = style_params.get("color", self.subs.color)
                self.subs.stroke_color = style_params.get("stroke_color", self.subs.stroke_color)
                self.subs.stroke_width = style_params.get("stroke_width", self.subs.stroke_width)

            subs_clip = self.subs.parse_srt(srt_path, video_clip.w)
            # Asegurarse de que los subtítulos estén centrados horizontalmente y en la parte inferior
            subs_clip = subs_clip.with_position(('center', 0.8), relative=True)
            return CompositeVideoClip([video_clip, subs_clip])
        except Exception as e:
            logger.error(f"Error agregando subtítulos: {e}")
            return video_clip

    def concatenate_chapters(
        self,
        video_paths: list[str],
        output_path: str,
        transition_duration: float = 1.0,
        fps: int = 24
    ) -> bool:
        """Concatena múltiples clips de video con transiciones suaves."""
        if not MOVIEPY_AVAILABLE:
            return False

        clips = []
        try:
            for path in video_paths:
                if os.path.exists(path):
                    clips.append(VideoFileClip(path))

            if not clips:
                return False

            if len(clips) == 1:
                shutil.copy(video_paths[0], output_path)
                return True

            # Aplicar transiciones (crossfade)
            final_clips = [clips[0]]
            for i in range(1, len(clips)):
                # Crossfade entre el clip anterior y el actual
                final_clips.append(clips[i].crossfadein(transition_duration))

            # Concatenar con padding para que las transiciones funcionen
            # MoviePy concatenate_videoclips con padding maneja el crossfade
            final_video = concatenate_videoclips(final_clips, method="compose", padding=-transition_duration)
            
            final_video.write_videofile(
                output_path,
                fps=fps,
                codec='libx264',
                audio_codec='aac',
                verbose=False,
                logger=None
            )
            return True

        except Exception as e:
            logger.error(f"Error concatenando capítulos: {e}")
            return False
        finally:
            for clip in clips:
                clip.close()

    def assemble_dynamic_video(
        self,
        base_image_path: str,
        audio_path: str,
        srt_path: str,
        output_path: str,
        use_ken_burns: bool = True,
        use_broll: bool = False,
        script_text: str = "",
        prefer_helios: bool = True,
        fps: int = 24,
        quality: str = "Alta",
        resolution: str = "1080p",
        soundtrack_path: str = None,
        soundtrack_volume: float = 0.15,
        subtitle_style: dict = None
    ) -> bool:
        if not MOVIEPY_AVAILABLE:
            logger.error("MoviePy no disponible.")
            return False

        # Validación de archivos de entrada
        if not os.path.exists(base_image_path):
            logger.error(f"Imagen base no encontrada: {base_image_path}")
            return False
        if not os.path.exists(audio_path):
            logger.error(f"Audio no encontrado: {audio_path}")
            return False
        
        # Configurar resolución y bitrate según calidad
        resolution_map = {
            "720p": (1280, 720),
            "1080p": (1920, 1080),
            "4K": (3840, 2160),
            "HD (720p)": (1280, 720),
            "Full HD (1080p)": (1920, 1080),
            "Ultra HD (4K)": (3840, 2160)
        }

        quality_bitrate_map = {
            "Básica": "1000k",
            "Estándar": "2500k",
            "Alta": "5000k",
            "Profesional": "10000k"
        }

        target_width, target_height = resolution_map.get(resolution, (1920, 1080))
        bitrate = quality_bitrate_map.get(quality, "5000k")

        audio_clip = None
        video_clip = None
        final_clip = None
        bg_music = None

        try:
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration

            # Generar clip de video
            video_clip = self._generate_video_clip(
                base_image_path, script_text, output_path, duration, use_ken_burns
            )

            # Redimensionar si es necesario
            if video_clip.size != (target_width, target_height):
                try:
                    video_clip = video_clip.resized(new_size=(target_width, target_height))
                except Exception:
                    # Fallback para versiones antiguas de MoviePy
                    video_clip = video_clip.resize(newsize=(target_width, target_height))

            # Añadir B-Roll si está habilitado
            video_clip = self._add_broll_if_enabled(video_clip, script_text)

            # Añadir subtítulos si están disponibles
            final_clip = self._add_subtitles_if_enabled(video_clip, srt_path, style_params=subtitle_style)

            # Manejar música de fondo
            final_audio = audio_clip
            if soundtrack_path and os.path.exists(soundtrack_path):
                try:
                    bg_music = AudioFileClip(soundtrack_path)
                    # Ajustar volumen y duración
                    bg_music = bg_music.with_volume_scaled(soundtrack_volume)
                    if bg_music.duration < duration:
                        bg_music = bg_music.loop(duration=duration)
                    else:
                        bg_music = bg_music.subclipped(0, duration)
                    
                    from moviepy import CompositeAudioClip
                    final_audio = CompositeAudioClip([audio_clip, bg_music])
                except Exception as e:
                    logger.error(f"Error al añadir música de fondo: {e}")

            # Añadir audio final
            final_clip = final_clip.with_audio(final_audio)

            # Renderizar con configuración avanzada
            final_clip.write_videofile(
                output_path,
                fps=fps,
                codec='libx264',
                audio_codec='aac',
                bitrate=bitrate,
                verbose=False,
                logger=None
            )
            logger.info(f"Video dinámico generado: {output_path} ({resolution}, {quality}, {fps}fps)")
            return True

        except Exception as e:
            logger.error(f"Error ensamblando video dinámico: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

        finally:
            # Cerrar clips
            self._close_video_clips(audio_clip, video_clip, final_clip, bg_music)
            # Limpiar temporales
            self._cleanup_temporary_files(output_path)
