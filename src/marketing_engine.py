# src/marketing_engine.py
"""
Motor de Marketing AI: generación de miniaturas clickbait y SEO automatizado.
"""

import os
import threading

from src.ai_engine import AIEngine
from src.image_engine import ImageEngine
from src.utils import logger


class ThumbnailGenerator:
    """Genera miniaturas estilo YouTube Clickbait usando IA de imágenes."""

    def __init__(self, config: dict, image_engine: ImageEngine):
        self.config = config
        self.image_engine = image_engine
        self.style_prompt = (
            "YouTube thumbnail, high contrast, dramatic lighting, "
            "close-up portrait with intense expression, bold text overlay style, "
            "vibrant colors, 8k, clickbait aesthetic, no text in image"
        )

    def generate_thumbnail_prompt(self, script: str, title: str = "") -> str:
        """
        Crea un prompt optimizado para miniatura basado en el guion/título.
        """
        # Extraer palabras clave
        keywords = []
        # Usar IA para generar un prompt detallado (podría ser con Groq)
        base = f"{self.style_prompt}. Content: {title[:100]}. Key elements: "
        # Versión simple: concatenar primeras frases
        snippet = script[:200].replace('\n', ' ')
        return f"{base} {snippet}"

    def generate(self, script: str, title: str = "", output_path: str | None = None) -> str | None:
        """
        Genera una imagen de miniatura y la guarda.
        """
        try:
            prompt = self.generate_thumbnail_prompt(script, title)
            img_bytes = self.image_engine.generate(prompt)
            if output_path is None:
                output_path = os.path.join(self.config.get("base_folder", os.getcwd()), "thumbnail.jpg")
            with open(output_path, "wb") as f:
                f.write(img_bytes)
            logger.info(f"Miniatura generada: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error generando miniatura: {e}")
            return None


class SEOGenerator:
    """Genera título, descripción y tags para plataformas sociales usando Groq."""

    def __init__(self, config: dict, ai_engine: AIEngine):
        self.config = config
        self.ai = ai_engine

    def generate_seo(self, script: str, serie: str, parte: int, emotion: str) -> dict[str, str]:
        """
        Retorna un diccionario con 'title', 'description', 'tags'.
        """
        prompt = f"""
Eres un experto en SEO para YouTube y TikTok. Basado en el siguiente guion de un video de misterio/ciencia ficción,
genera:
1. Un título llamativo (máximo 60 caracteres) que incluya la serie "{serie}".
2. Una descripción optimizada (2-3 frases, incluyendo hashtags relevantes).
3. Una lista de 10 tags separados por comas.

Serie: {serie} - Parte {parte}
Emoción principal: {emotion}
Guion:
{script[:1500]}

Responde en formato JSON con las claves "title", "description", "tags".
"""
        result = {"title": f"{serie} - Parte {parte}", "description": "", "tags": ""}
        try:
            # Usar método síncrono ficticio (en producción sería con callback)
            response = [None]
            event = threading.Event()

            def callback(text, ok, cancelled):
                response[0] = (text, ok, cancelled)
                event.set()

            self.ai.generate_script(prompt, callback)
            event.wait(timeout=30)
            text, ok, cancelled = response[0]
            if ok and not cancelled:
                import json
                # Intentar parsear JSON (puede venir con markdown)
                text = text.strip()
                if text.startswith("```json"):
                    text = text[7:-3]
                elif text.startswith("```"):
                    text = text[3:-3]
                data = json.loads(text)
                result.update(data)
        except Exception as e:
            logger.error(f"Error generando SEO: {e}")
        return result


class MarketingEngine:
    """Motor principal de marketing."""

    def __init__(self, config: dict, ai: AIEngine, image_engine: ImageEngine):
        self.config = config
        self.ai = ai
        self.image_engine = image_engine
        self.thumbnail_gen = ThumbnailGenerator(config, image_engine)
        self.seo_gen = SEOGenerator(config, ai)

    def generate_marketing_assets(
        self,
        script: str,
        serie: str,
        parte: int,
        emotion: str,
        output_dir: str
    ) -> dict[str, str]:
        """
        Genera miniatura y metadatos SEO para un capítulo.
        """
        result = {
            "thumbnail": "",
            "title": "",
            "description": "",
            "tags": ""
        }
        # Miniatura
        thumb_path = os.path.join(output_dir, f"thumbnail_{serie}_P{parte}.jpg")
        result["thumbnail"] = self.thumbnail_gen.generate(script, title=f"{serie} P{parte}", output_path=thumb_path) or ""

        # SEO
        seo_data = self.seo_gen.generate_seo(script, serie, parte, emotion)
        result.update(seo_data)

        # Guardar metadatos en archivo
        meta_path = os.path.join(output_dir, f"metadata_{serie}_P{parte}.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            import json
            json.dump(result, f, indent=2, ensure_ascii=False)

        return result
