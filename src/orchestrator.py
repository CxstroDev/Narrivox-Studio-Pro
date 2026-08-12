# src/orchestrator.py
"""
Orquestador de procesamiento masivo (Marathon+).
Permite generar múltiples capítulos en paralelo y exportar en formatos vertical/horizontal.
"""

import concurrent.futures
import os
import threading
from collections.abc import Callable

from src.ai_engine import AIEngine
from src.cinematic_engine import CinematicEngine
from src.data_manager import DataManager
from src.image_engine import ImageEngine
from src.sound_engine import SoundEngine
from src.tts_engine import TTSEngine
from src.utils import logger

# Verificar MoviePy para reescalado
try:
    from moviepy import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False


class FormatConverter:
    """Convierte videos entre formatos (16:9 horizontal y 9:16 vertical)."""

    @staticmethod
    def to_vertical(input_path: str, output_path: str, target_width: int = 1080, target_height: int = 1920) -> bool:
        """Convierte un video horizontal a vertical centrado con recorte."""
        if not MOVIEPY_AVAILABLE:
            return False
        try:
            clip = VideoFileClip(input_path)
            # Calcular recorte central
            src_w, src_h = clip.size
            target_aspect = target_width / target_height
            src_aspect = src_w / src_h

            if src_aspect > target_aspect:
                # Recortar horizontalmente
                new_w = int(src_h * target_aspect)
                x_center = src_w / 2
                clip = clip.crop(x1=x_center - new_w/2, width=new_w)
            else:
                # Recortar verticalmente
                new_h = int(src_w / target_aspect)
                y_center = src_h / 2
                clip = clip.crop(y1=y_center - new_h/2, height=new_h)

            clip = clip.resize(newsize=(target_width, target_height))
            clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
            logger.info(f"Video vertical exportado: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error convirtiendo a vertical: {e}")
            return False

    @staticmethod
    def to_horizontal(input_path: str, output_path: str, target_width: int = 1920, target_height: int = 1080) -> bool:
        """Convierte un video vertical a horizontal (similar lógica)."""
        if not MOVIEPY_AVAILABLE:
            return False
        try:
            clip = VideoFileClip(input_path)
            src_w, src_h = clip.size
            target_aspect = target_width / target_height
            src_aspect = src_w / src_h

            if src_aspect < target_aspect:
                new_h = int(src_w / target_aspect)
                y_center = src_h / 2
                clip = clip.crop(y1=y_center - new_h/2, height=new_h)
            else:
                new_w = int(src_h * target_aspect)
                x_center = src_w / 2
                clip = clip.crop(x1=x_center - new_w/2, width=new_w)

            clip = clip.resize(newsize=(target_width, target_height))
            clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
            logger.info(f"Video horizontal exportado: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error convirtiendo a horizontal: {e}")
            return False


class ChapterGenerator:
    """Genera un capítulo completo (guion, audio, imagen, video) para una serie/parte."""

    def __init__(self, config: dict, ai: AIEngine, tts: TTSEngine, data: DataManager, 
                 image_engine: ImageEngine = None, cinematic_engine: CinematicEngine = None):
        self.config = config
        self.ai = ai
        self.tts = tts
        self.data = data
        self.image_engine = image_engine or ImageEngine(config)
        self.cinematic = cinematic_engine or CinematicEngine(config)
        self.sound = SoundEngine(config)

    def generate_chapter(
        self,
        serie: str,
        parte: int,
        prompt_data: dict,
        voice_display_name: str,
        emotion: str,
        progress_callback: Callable[[str, float], None] | None = None
    ) -> dict[str, any]:
        """
        Genera todos los activos para un capítulo.

        Returns:
            Diccionario con rutas generadas y estado.
        """
        result = {
            "serie": serie,
            "parte": parte,
            "success": False,
            "script": "",
            "audio_path": "",
            "image_path": "",
            "video_path": ""
        }

        def report(msg, progress):
            logger.info(f"[{serie} P{parte}] {msg}")
            if progress_callback:
                progress_callback(f"{serie} P{parte}: {msg}", progress)

        try:
            # 1. Generar guion
            report("Generando guion...", 0.1)
            prompt = self.ai.format_prompt(self.config.get("prompt_template", ""), prompt_data)
            # Nota: generate_script_with_context requiere callback; aquí usamos una versión síncrona ficticia.
            # En producción, usaríamos threading para esperar resultado.
            # Simplificación: usamos un método síncrono auxiliar (no implementado en AIEngine actual)
            # Para este ejemplo, asumimos que generate_script_with_context puede ejecutarse en un hilo y esperamos.
            script_result = [None]
            event = threading.Event()

            def script_callback(text, ok, cancelled):
                script_result[0] = (text, ok, cancelled)
                event.set()

            system_msg = "Eres un guionista experto."
            self.ai.generate_script_with_context(system_msg, prompt, script_callback)
            event.wait(timeout=60)
            
            if script_result[0] is None:
                raise Exception("Tiempo de espera agotado generando el guion (timeout 60s)")
                
            text, ok, cancelled = script_result[0]
            if not ok or cancelled:
                raise Exception(f"Fallo en generación de guion: {text if text else 'Cancelado'}")
            result["script"] = text

            # 2. Crear carpeta del proyecto
            folder = self.data.create_project_folder(serie, str(parte))
            s_clean = self.data.clean_filename(serie)

            # 3. Generar audio
            report("Generando narración...", 0.3)
            audio_path = os.path.join(folder, f"Narracion_{s_clean}_P{parte}.mp3")
            voice_code = self.tts.get_voice_code(voice_display_name, "Todos")
            srt_content = self.tts.generate_audio(text, audio_path, voice_code)
            result["audio_path"] = audio_path

            # 4. Generar imagen
            report("Generando arte visual...", 0.5)
            visual_prompt_template = self.config.get("visual_prompt_template", "")
            visual_prompt = self.ai.format_prompt(visual_prompt_template, {"estilo": "Fotorrealista", "guion": text})
            # Usamos el motor de imagen (síncrono en hilo aparte)
            img_bytes = self.image_engine.generate(visual_prompt)
            image_path = os.path.join(folder, f"Imagen_{s_clean}_P{parte}.jpg")
            with open(image_path, "wb") as f:
                f.write(img_bytes)
            result["image_path"] = image_path

            # 5. Guardar subtítulos
            if srt_content:
                srt_path = os.path.join(folder, f"Subtitulos_{s_clean}_P{parte}.srt")
                with open(srt_path, "w", encoding="utf-8") as f:
                    f.write(srt_content)
            else:
                srt_path = ""

            # 6. Mezclar sonido (música de fondo)
            report("Mezclando paisaje sonoro...", 0.7)
            mixed_audio = self.sound.generate_soundtrack(audio_path, emotion, output_path=audio_path.replace(".mp3", "_mixed.mp3"))
            final_audio = mixed_audio if mixed_audio else audio_path

            # 7. Ensamblar video dinámico
            report("Renderizando video...", 0.85)
            video_path = os.path.join(folder, f"Video_{s_clean}_P{parte}.mp4")
            self.cinematic.assemble_dynamic_video(
                base_image_path=image_path,
                audio_path=final_audio,
                srt_path=srt_path,
                output_path=video_path,
                use_ken_burns=True,
                use_broll=self.config.get("enable_broll", False),
                script_text=text
            )
            result["video_path"] = video_path

            # 8. Guardar proyecto en BD
            report("Guardando en base de datos...", 0.95)
            self.data.save_project({
                "Fecha": "",  # Se genera en data_manager
                "Serie": serie,
                "Parte": parte,
                "Tema": prompt_data.get("tema", ""),
                "Objeto": prompt_data.get("objeto", ""),
                "Anomalía": prompt_data.get("anomalia", ""),
                "Emoción": emotion,
                "Tono": prompt_data.get("tono", ""),
                "Estructura": prompt_data.get("estructura", ""),
                "Estado": "Listo",
                "Carpeta": folder
            })

            result["success"] = True
            report("Capítulo completado.", 1.0)
            return result

        except Exception as e:
            logger.error(f"Error en capítulo {serie} P{parte}: {e}")
            result["error"] = str(e)
            return result


class Orchestrator:
    """Gestiona la generación masiva de capítulos en paralelo."""

    def __init__(self, config: dict, ai: AIEngine, tts: TTSEngine, data: DataManager,
                 image_engine: ImageEngine = None, cinematic_engine: CinematicEngine = None):
        self.config = config
        self.ai = ai
        self.tts = tts
        self.data = data
        self.generator = ChapterGenerator(config, ai, tts, data, image_engine, cinematic_engine)
        self.current_project = None  # Almacena el último proyecto generado o seleccionado

    def generate_series(
        self,
        serie: str,
        num_parts: int,
        base_prompt_data: dict,
        voice_name: str,
        emotion: str,
        max_workers: int = 4,
        progress_callback: Callable[[str, float], None] | None = None
    ) -> list[dict]:
        """
        Genera múltiples capítulos en paralelo usando ThreadPoolExecutor.
        """
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for part in range(1, num_parts + 1):
                # Modificar datos de prompt para esta parte (ej. añadir "Parte X")
                part_data = base_prompt_data.copy()
                part_data["parte"] = part
                future = executor.submit(
                    self.generator.generate_chapter,
                    serie, part, part_data, voice_name, emotion,
                    None  # Podríamos pasar un callback por capítulo
                )
                futures[future] = part

            for future in concurrent.futures.as_completed(futures):
                part = futures[future]
                try:
                    res = future.result()
                    results.append(res)
                    if progress_callback:
                        completed = len(results)
                        progress_callback(f"Completado {completed}/{num_parts}", completed / num_parts)
                except Exception as e:
                    logger.error(f"Error en parte {part}: {e}")
                    results.append({"serie": serie, "parte": part, "success": False, "error": str(e)})
        return results
